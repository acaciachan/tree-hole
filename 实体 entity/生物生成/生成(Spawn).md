
# 1. 生成(spawn)是如何触发的？
```java
private void tickChunks() {
	long l = this.level.getGameTime();
	long m = l - this.lastInhabitedUpdate;
	this.lastInhabitedUpdate = l;
	if (!this.level.isDebug()) {
		ProfilerFiller profilerFiller = Profiler.get();
		profilerFiller.push("pollingChunks");
		if (this.level.tickRateManager().runsNormally()) {
			List<LevelChunk> list = this.tickingChunks;

			try {
				profilerFiller.push("filteringTickingChunks");
				this.collectTickingChunks(list);
				profilerFiller.popPush("shuffleChunks");
				Util.shuffle(list, this.level.random); // 随机打乱
				this.tickChunks(profilerFiller, m, list);  //注意这里，执行区块运算
				profilerFiller.pop();
			} finally {
				list.clear();
			}
		}

		this.broadcastChangedChunks(profilerFiller);
		profilerFiller.pop();
	}
}
```

我们可以看到区块运算前的步骤：

1. 获取所有的实体运算的区块

2. 随机打乱

3. 依次(上述打乱后的顺序)执行区块运算(tickChunks()函数)

下面来看tickChunks，也就是真正的区块运算的实现：

```java
private void tickChunks(ProfilerFiller profilerFiller, long l, List<LevelChunk> list) {
	profilerFiller.popPush("naturalSpawnCount");
	int i = this.distanceManager.getNaturalSpawnChunkCount();
	NaturalSpawner.SpawnState spawnState = NaturalSpawner.createState(
		i, this.level.getAllEntities(), this::getFullChunk, new LocalMobCapCalculator(this.chunkMap)
	);
	this.lastSpawnState = spawnState;
	profilerFiller.popPush("spawnAndTick");
	boolean bl = this.level.getGameRules().getBoolean(GameRules.RULE_DOMOBSPAWNING);
	int j = this.level.getGameRules().getInt(GameRules.RULE_RANDOMTICKING);
	
	// 获取需要进行自然生成的实体种类
	List<MobCategory> list2;
	if (bl && (this.spawnEnemies || this.spawnFriendlies)) {
		boolean bl2 = this.level.getLevelData().getGameTime() % 400L == 0L; 
		// 每隔400tick bl2值才会变成一次true，用于定期触发生成“持久不消失”的生物(目前只有creature)
		list2 = NaturalSpawner.getFilteredSpawningCategories(spawnState, this.spawnFriendlies, this.spawnEnemies, bl2); // 获取需要自然生成的实体种类
	} else {
		list2 = List.of();
	}

	// 遍历所有需要运算的区块
	for (LevelChunk levelChunk : list) {
		ChunkPos chunkPos = levelChunk.getPos();
		levelChunk.incrementInhabitedTime(l);

		// 自然生成
		if (!list2.isEmpty() && this.level.getWorldBorder().isWithinBounds(chunkPos)) {
			NaturalSpawner.spawnForChunk(this.level, levelChunk, spawnState, list2);
		}

		// 区块刻
		if (this.level.shouldTickBlocksAt(chunkPos.toLong())) {
			this.level.tickChunk(levelChunk, j);
		}
	}
	
	// 自定义生成(游商、幻翼、村民刷猫、僵尸围城、袭击小队)
	profilerFiller.popPush("customSpawners");
	if (bl) {
		this.level.tickCustomSpawners(this.spawnEnemies, this.spawnFriendlies);
	}
}
```

可以看到，整个流程分为三步：

1. 获取需要自然生成(NaturalSpawn)的生物种类
	一般生物每tick都会生成
	持久不消失的生物(creature)每400tick才生成一次

2. 遍历所有需要运算的区块：自然生成(NaturalSpawn)和区块刻

3. 每个维度的自定义生成(CustomSpawn)

# 2. 自然生成(NaturalSpawn)

## 2.1 自然生成相关知识

### 2.1.1 生物种类(MobCategory)

在此之前我门需要首先了Mojang划分的生物种类(MobCategory)有哪些：net.minecraft.world.entity.MobCategory

整理成表格:

|Name						|名字					|上限	|持久			|立即消失距离		|友好			|
|:-							|:-						|:-		|:-				|:-					|:-				|
|							|						|(max)	|(isPersistent)	|(despawnDistance)	|(isFriendly)	|
|monster					|怪物					|70		|false			|128				|false			|
|creature					|动物					|10		|true			|128				|true			|
|ambient					|环境(蝙蝠)				|15		|false			|128				|true			|
|water_ambient				|水生环境(桶装鱼)		|20		|false			|64					|true			|
|water_creature				|水生生物(鱿鱼、海豚)	|5		|false			|128				|true			|
|underground_water_creature	|地下水生生物(发光鱿鱼)	|5		|false			|128				|true			|
|axolotls					|美西螈					|5		|false			|128				|true			|
|misc						|杂项					|-1		|true			|128				|true			|

1. 其中杂项(misc)类似于Others，不参与自然生成

2. 友好(isFriendly)表示是否为友好生物。目前只有动物(creature)是true

3. 持久(isPersistent)表示是否为持久存在不消失的生物。目前只有动物(creature)和杂项(misc)是true

4. 立即消失距离(despawnDistance)表示距离最近玩家超过这个距离就会**立即消失**

5. 不消失距离(noDespawnDistance)表示距离最近玩家超过这个距离就**可以随机消失**，有玩家在这个范围内则不会

6. 上限(max)表示单玩家附近最大的生物数量

7. 具体某种实体属于哪一类，去这里查看：net.minecraft.world.entity.EntityType

## 2.1.2 生物消失(despawn)：
Mob类(重点)：net.minecraft.world.entity.Mob#checkDespawn
```java
    public void checkDespawn() {
        if (this.level().getDifficulty() == Difficulty.PEACEFUL && this.shouldDespawnInPeaceful()) {
            this.discard();
        } else if (!this.isPersistenceRequired() && !this.requiresCustomPersistence()) {
            Entity entity = this.level().getNearestPlayer(this, -1.0);
            if (entity != null) {
                double d = entity.distanceToSqr(this);
                int i = this.getType().getCategory().getDespawnDistance();
                int j = i * i;
                if (d > j && this.removeWhenFarAway(d)) {
                    this.discard();
                }

                int k = this.getType().getCategory().getNoDespawnDistance();
                int l = k * k;
                if (this.noActionTime > 600 && this.random.nextInt(800) == 0 && d > l && this.removeWhenFarAway(d)) {
                    this.discard();
                } else if (d < l) {
                    this.noActionTime = 0;
                }
            }
        } else {
            this.noActionTime = 0;
        }
    }
```

细节解释：

1. this.shouldDespawnInPeaceful()：
	怪物(Monster)：true
	恶魂，幻翼：true
	史莱姆：return size > 0
	猪灵：false
	其它：false

2. persistenceRequired
	相关的方法：
		isPersistenceRequired() { return this.persistenceRequired; }
		setPersistenceRequired() { this.persistenceRequired = true; }

	persistenceRequired
		默认为false
		以下情况会被设置为true：
			
			当生物(Mob)捡起掉落物
			命名牌命名的的生物
			
			被驯服
			繁殖的悦灵、美西螈、疣猪兽
			蝌蚪方块生成的蝌蚪、蝌蚪长成的青蛙
			
			猪被雷劈后的僵尸猪灵
			远古守卫者
			陷阱马和陷阱骷髅
			
			村庄生成的猫
			村民生成的女巫和僵尸村民
			试炼刷怪笼生成的生物

			结构怪物（世界生成的时候伴随生成的第一个生物）：
				海底废墟生成的溺尸
				女巫小屋伴随生成的第一个女巫和猫
				林地府邸生成的怪物


3. this.requiresCustomPersistence()
	Mob：return this.isPassenger()
		美西螈：this.isPassenger() || this.fromBucket()
		末影人：this.isPassenger() || this.getCarriedBlock() != null
		袭击相关生物：this.isPassenger() || this.getCurrentRaid() != null

4. this.removeWhenFarAway(d)
	Mob类生物默认为true
	但有Mob类以下特例(override)：
		1. 此类直接false，即不会过远消失：动物(Animal)、傀儡类、悦灵

		2. 看条件消失
		鸡：return this.isChickenJockey()
		猫：return !this.isTame() && this.tickCount > 2400
		豹猫：return !this.isTrusting() && this.tickCount > 2400
		桶装鱼和美西螈：return !this.fromBucket() && !this.hasCustomName()
		僵尸村民：return !this.isConverting() && this.villagerXp == 0
		
		3. 此类生物会因为正在进行的事情而获得持久存在的标签
		疣猪兽：return !this.isPersistenceRequired()
		猪灵：return !this.isPersistenceRequired()
		坚守者：return !this.isPersistenceRequired()
		
		4. 正在参加袭击的生物、灾厄巡逻队不会消失
		灾厄巡逻队：return !this.patrolling || d > 16384.0 (d是传进来的参数，表示距离最近玩家距离) 
			袭击队伍：return this.getCurrentRaid() == null ? super.removeWhenFarAway(d) : false

5. entityType.getCategory().getNoDespawnDistance()
	return 32

6. entityType.canSpawnFarFromPlayer()
	true：动物类("creature")，杂项类("misc")，掠夺者(pillager)，潜影贝(shulker)
	false：其余所有

7. noActionTime
	以下情况下会归零：
		livingEntity 不免疫伤害而受伤 (来源：net.minecraft.world.entity.LivingEntity#hurtServer)
		玩家(player)不免疫伤害而受伤 (来源：net.minecraft.world.entity.player.Player#hurtServer)

		Mob 距离最近玩家距离小于32 (来源：net.minecraft.world.entity.Mob#checkDespawn)
		Mob 满足 this.isPersistenceRequired() && this.requiresCustomPersistence() (来源：net.minecraft.world.entity.Mob#checkDespawn)
		凋零 不在和平模式 (来源：net.minecraft.world.entity.boss.wither.WitherBoss#checkDespawn)
		掠夺者(pillager) 在拉弩 (来源：net.minecraft.world.entity.monster.Pillager#onCrossbowAttackPerformed)
		猪灵 在拉弩 (来源：net.minecraft.world.entity.monster.piglin.Piglin#onCrossbowAttackPerformed)
		袭击者(Raider)在袭击中 (来源：net.minecraft.world.entity.raid.Raider#aiStep)

	以下情况会增加：
		Mob 每tick的ai运算会 noActionTime++ (来源：net.minecraft.world.entity.Mob#serverAiStep)
		Monster 每tick，如果光照幻数>0.5，即实际亮度(主世界 <= 12, 下界 < 12)时，noActionTime += 2 (来源：net.minecraft.world.entity.monster.Monster#updateNoActionTime)

	在 Mob 的 checkDespawn 里面，如果 ActionTime > 600tick(30s) 时，才有机会执行随机消失的代码

分析生物的消失：
1. 如果难度为和平模式，并且生物在和平难度下消失(shouldDespawnInPeaceful)，则直接消失。

2. 如果生物因为各种原因带上了(setPersistenceRequired)持久属性，则不会消失，且noActionTime设置为0。

3. 如果没有阻止消失的属性，距离最近玩家距离 d>128，且满足过远消失条件(removeWhenFarAway(d))，则生物消失。
	
4. 如果没有阻止消失的属性，则距离最近玩家距离d>32，且会过远消失(上文提到的removeWhenFarAway(d))，
	
	那么 noActionTime > 600tick(30s) 时，每tick有1/800的概率消失
	
	(期望40s，半衰期log(0.5, 1-1/800)≈27.7s)。

	否则如果距离最近玩家距离d<32，noActionTime重置为0。

5. 凋灵在和平模式而消失，否则非和平模式noActionTime设置为0；末影龙不会消失；潜影贝的子弹在和平模式也会消失。

### 2.1.3 高度图(Heightmap)

	(HeightMap数值对应的y坐标方块是目标方块上方的方块)


## 2.2 自然生成的原点位置

之前提到的区块运算(tickChunks)方法里面，对于每个区块都会进行自然生成(spawnForChunk)和区块刻(tickChunk)，
我们继续研究区块自然生成，即spawnForChunk:

```java
public static void spawnForChunk(ServerLevel serverLevel, LevelChunk levelChunk, NaturalSpawner.SpawnState spawnState, List<MobCategory> list) {
	ProfilerFiller profilerFiller = Profiler.get();
	profilerFiller.push("spawner");

	for (MobCategory mobCategory : list) {
		if (spawnState.canSpawnForCategoryLocal(mobCategory, levelChunk.getPos())) {
			spawnCategoryForChunk(mobCategory, serverLevel, levelChunk, spawnState::canSpawn, spawnState::afterSpawn); // 依次对列表中每种生物类型的进行生成
		}
	}

	profilerFiller.pop();
}

public static void spawnCategoryForChunk(
	MobCategory mobCategory,
	ServerLevel serverLevel,
	LevelChunk levelChunk,
	NaturalSpawner.SpawnPredicate spawnPredicate,
	NaturalSpawner.AfterSpawnCallback afterSpawnCallback
) {
	BlockPos blockPos = getRandomPosWithin(serverLevel, levelChunk); // 获取一个随机生成点
	if (blockPos.getY() >= serverLevel.getMinY() + 1) {
		spawnCategoryForPosition(mobCategory, serverLevel, levelChunk, blockPos, spawnPredicate, afterSpawnCallback);
	}
}

private static BlockPos getRandomPosWithin(Level level, LevelChunk levelChunk) {
	ChunkPos chunkPos = levelChunk.getPos();
	int i = chunkPos.getMinBlockX() + level.random.nextInt(16);
	int j = chunkPos.getMinBlockZ() + level.random.nextInt(16);
	int k = levelChunk.getHeight(Heightmap.Types.WORLD_SURFACE, i, j) + 1;
	int l = Mth.randomBetweenInclusive(level.random, level.getMinY(), k);
	return new BlockPos(i, l, j);
}

public static int randomBetweenInclusive(RandomSource randomSource, int i, int j) {
	return randomSource.nextInt(j - i + 1) + i;
}

```
将上述代码总结成伪代码：
```java
区块运算：
	获取需要自然生成的生物种类
		1. 数量未到总量上限的生物种类
		2. 持久类生物(动物)每400tick才刷一次
	每个区块(chunk)：
		每种需要生成的生物种类(MobCategory)：
			随机获取区块内的一个位置
				x0,z0 为区块内随机的一个水平位置
				y0 为(x0,z0)位置随机选一个方块：维度最低方块 ~ 最高非空气方块上方的空气
			在(x0,y0,z0)位置生成生物(spawnCategoryForPosition)
```

## 2.3 自然生成的实现

```java
public static void spawnCategoryForPosition(
	MobCategory mobCategory,
	ServerLevel serverLevel,
	ChunkAccess chunkAccess,
	BlockPos blockPos,
	NaturalSpawner.SpawnPredicate spawnPredicate,
	NaturalSpawner.AfterSpawnCallback afterSpawnCallback
) {
	StructureManager structureManager = serverLevel.structureManager();
	ChunkGenerator chunkGenerator = serverLevel.getChunkSource().getGenerator();
	int i = blockPos.getY();
	BlockState blockState = chunkAccess.getBlockState(blockPos);
	if (!blockState.isRedstoneConductor(chunkAccess, blockPos)) {
		BlockPos.MutableBlockPos mutableBlockPos = new BlockPos.MutableBlockPos();
		int j = 0;

		for (int k = 0; k < 3; k++) { // 三组从原点出发的随机游走
			int l = blockPos.getX();
			int m = blockPos.getZ();
			int n = 6;
			MobSpawnSettings.SpawnerData spawnerData = null;
			SpawnGroupData spawnGroupData = null;
			int o = Mth.ceil(serverLevel.random.nextFloat() * 4.0F);
			int p = 0; 

			for (int q = 0; q < o; q++) { // 每组随机游走
				l += serverLevel.random.nextInt(6) - serverLevel.random.nextInt(6);
				m += serverLevel.random.nextInt(6) - serverLevel.random.nextInt(6);
				mutableBlockPos.set(l, i, m);
				double d = l + 0.5;
				double e = m + 0.5; // 游走(位置移动到此方块的底部中心，此位置记作 M)
				Player player = serverLevel.getNearestPlayer(d, i, e, -1.0, false); // 最近的非旁观者玩家
				if (player != null) {
					double f = player.distanceToSqr(d, i, e); // M与最近玩家的距离(的平方)
					if (isRightDistanceToPlayerAndSpawnPoint(serverLevel, chunkAccess, mutableBlockPos, f)) { // 此次随机游走后的位置满足：距离玩家<=24 && 距离出生点<24 && (当前位置位还在原点区块 || 当前位置区块强加载)
						if (spawnerData == null) { // 获取P点的可生成生物种类，并随机(有不同权重)抽一个(如果还没获取过)
							Optional<MobSpawnSettings.SpawnerData> optional = getRandomSpawnMobAt(
								serverLevel, structureManager, chunkGenerator, mobCategory, serverLevel.random, mutableBlockPos
							);
							if (optional.isEmpty()) { // 什么都不能生成，就直接终止这组游走
								break;
							}

							spawnerData = optional.get(); // spawnerData设置为刚刚抽到的生物及其信息
							o = spawnerData.minCount() + serverLevel.random.nextInt(1 + spawnerData.maxCount() - spawnerData.minCount()); // o 游走的次数(也是这组游走的尝试生成数量)：随机取该生物的成组刷出的最小数量~最大数量
						}

						if (isValidSpawnPostitionForType(serverLevel, mobCategory, structureManager, chunkGenerator, spawnerData, mutableBlockPos, f)
							&& spawnPredicate.test(spawnerData.type(), mutableBlockPos, chunkAccess)) {
							Mob mob = getMobForSpawn(serverLevel, spawnerData.type());
							if (mob == null) {
								return;
							}

							mob.snapTo(d, i, e, serverLevel.random.nextFloat() * 360.0F, 0.0F);
							if (isValidPositionForMob(serverLevel, mob, f)) {
								spawnGroupData = mob.finalizeSpawn(
									serverLevel, serverLevel.getCurrentDifficultyAt(mob.blockPosition()), EntitySpawnReason.NATURAL, spawnGroupData
								);
								j++;
								p++;
								serverLevel.addFreshEntityWithPassengers(mob);
								afterSpawnCallback.run(mob, chunkAccess);
								if (j >= mob.getMaxSpawnClusterSize()) {
									return;
								}

								if (mob.isMaxGroupSizeReached(p)) {
									break;
								}
							}
						}
					}
				}
			}
		}
	}
}


//下面来挨个看刷怪核心部分相关的方法：
	// 1. 阻止在玩家和出生点24米内刷怪
	private static boolean isRightDistanceToPlayerAndSpawnPoint(
		ServerLevel serverLevel, ChunkAccess chunkAccess, BlockPos.MutableBlockPos mutableBlockPos, double d
	) {
		if (d <= 576.0) {
			return false;
		} else {
			return serverLevel.getSharedSpawnPos()
					.closerToCenterThan(new Vec3(mutableBlockPos.getX() + 0.5, mutableBlockPos.getY(), mutableBlockPos.getZ() + 0.5), 24.0)
				? false
				: Objects.equals(new ChunkPos(mutableBlockPos), chunkAccess.getPos()) || serverLevel.isNaturalSpawningAllowed(mutableBlockPos);
		}
	}
	// 分析可得返回true的条件是: 距离玩家>24.0 && 距离出生点>=24.0 && (当前位置还在生成原点的区块 || 当前位置强加载))


	// 2. 与当前位置的可生成生物列表相关(都使用了mobsAt方法获取列表)
		// 2.1.1 随机获取一个能在当前位置生成的生物的代码，mobsAt方法：
		private static Optional<MobSpawnSettings.SpawnerData> getRandomSpawnMobAt(
			ServerLevel serverLevel,
			StructureManager structureManager,
			ChunkGenerator chunkGenerator,
			MobCategory mobCategory,
			RandomSource randomSource,
			BlockPos blockPos
		) {
			Holder<Biome> holder = serverLevel.getBiome(blockPos);
			return mobCategory == MobCategory.WATER_AMBIENT && holder.is(BiomeTags.REDUCED_WATER_AMBIENT_SPAWNS) && randomSource.nextFloat() < 0.98F
				? Optional.empty()
				: mobsAt(serverLevel, structureManager, chunkGenerator, mobCategory, blockPos, holder).getRandom(randomSource);
		}

		// 2.1.2 验证当前生物同样也是在新的位置可生成列表里的
		private static boolean canSpawnMobAt(
			ServerLevel serverLevel,
			StructureManager structureManager,
			ChunkGenerator chunkGenerator,
			MobCategory mobCategory,
			MobSpawnSettings.SpawnerData spawnerData,
			BlockPos blockPos
		) {
			return mobsAt(serverLevel, structureManager, chunkGenerator, mobCategory, blockPos, null).contains(spawnerData);
		}
	
		// 2.2 mobsAt方法：
		private static WeightedList<MobSpawnSettings.SpawnerData> mobsAt(
			ServerLevel serverLevel,
			StructureManager structureManager,
			ChunkGenerator chunkGenerator,
			MobCategory mobCategory,
			BlockPos blockPos,
			@Nullable Holder<Biome> holder
		) {
			return isInNetherFortressBounds(blockPos, serverLevel, mobCategory, structureManager)
				? NetherFortressStructure.FORTRESS_ENEMIES
				: chunkGenerator.getMobsAt(holder != null ? holder : serverLevel.getBiome(blockPos), structureManager, mobCategory, blockPos);
		}

		public static boolean isInNetherFortressBounds(BlockPos blockPos, ServerLevel serverLevel, MobCategory mobCategory, StructureManager structureManager) {
			if (mobCategory == MobCategory.MONSTER && serverLevel.getBlockState(blockPos.below()).is(Blocks.NETHER_BRICKS)) {
				Structure structure = structureManager.registryAccess().lookupOrThrow(Registries.STRUCTURE).getValue(BuiltinStructures.FORTRESS);
				return structure == null ? false : structureManager.getStructureAt(blockPos, structure).isValid();
			} else {
				return false;
			}
		}

		/*	
			如果当前位置在下界堡垒的"外结构"且下方方块是地狱砖(Blocks.NETHER_BRICKS)，
			则返回下界堡垒特有怪物，否则就返回正常的getMobsAt获取的怪物
				(下界堡垒的外结构不含下界堡垒的特殊怪物，只有内结构才有。
				这里的特判使得如果生成位置下方是下界砖，在下界堡垒外结构也能刷那些特殊生物)
			否则返回的就是，该点处根据自然结构和生物群系获取的怪物列表
			(自然结构的json文件里面都是"spawn_overrides"，也就是如果这一项不为空的话，结构的生物列表会完全覆盖掉生物群系的生物列表)
		 */


	// 2.3 检查此生物能否在当前位置生成

		// 这部分内容留在后面生物生成的判定时统一说明

	// 2.4 能否生成(spawnPredicate::canSpawn)

		spawnPredicate.test(spawnerData.type(), mutableBlockPos, chunkAccess)
		// 实际上就是
		canSpawn(spawnerData.type(), mutableBlockPos, chunkAccess)
		// canSpawn()作用是判断生物能否在当前的生成势能场景下生成
		private boolean canSpawn(EntityType<?> entityType, BlockPos blockPos, ChunkAccess chunkAccess) {
            this.lastCheckedPos = blockPos;
            this.lastCheckedType = entityType;
            MobSpawnSettings.MobSpawnCost mobSpawnCost = NaturalSpawner.getRoughBiome(blockPos, chunkAccess).getMobSettings().getMobSpawnCost(entityType);
            if (mobSpawnCost == null) {
                this.lastCharge = 0.0;
                return true;
            } else {
                double d = mobSpawnCost.charge();
                this.lastCharge = d;
                double e = this.spawnPotential.getPotentialEnergyChange(blockPos, d);
                return e <= mobSpawnCost.energyBudget();
            }
        }
		
		public double getPotentialEnergyChange(BlockPos blockPos, double d) {
			if (d == 0.0) {
				return 0.0;
			} else {
				double e = 0.0;

				for (PotentialCalculator.PointCharge pointCharge : this.charges) {
					e += pointCharge.getPotentialChange(blockPos);
				}

				return e * d;
			}
		}
		/*
			mobSpawnCost.charge = 生成势能
				灵魂沙峡谷(0.7)：末影人、恶魂、骷髅、炽足兽
				诡异丛林(1.0)：末影人
			mobSpawnCost.energyBudget = 生成预算
				灵魂沙峡谷(0.15)：末影人、恶魂、骷髅、炽足兽
				诡异丛林(0.12)：末影人
			
			计算生物当前位置的势能E
			E = this.mobSpawnCost.charge * ∑(附近所有生物)(that.mobSpawnCost.charge / this2thatDistance)
			若E <= this.mobSpawnCost.energyBudget，则返回true
		*/

		/* 生成生物之后更新怪物对世界的影响(afterSpawn)
			更新刷怪势能列表
			更新该生物种类的存在数量列表
		*/
		private void afterSpawn(Mob mob, ChunkAccess chunkAccess) {
            EntityType<?> entityType = mob.getType();
            BlockPos blockPos = mob.blockPosition();
            double d;
            if (blockPos.equals(this.lastCheckedPos) && entityType == this.lastCheckedType) {
                d = this.lastCharge;
            } else {
                MobSpawnSettings.MobSpawnCost mobSpawnCost = NaturalSpawner.getRoughBiome(blockPos, chunkAccess).getMobSettings().getMobSpawnCost(entityType);
                if (mobSpawnCost != null) {
                    d = mobSpawnCost.charge();
                } else {
                    d = 0.0;
                }
            }

            this.spawnPotential.addCharge(blockPos, d);
            MobCategory mobCategory = entityType.getCategory();
            this.mobCategoryCounts.addTo(mobCategory, 1);
            this.localMobCapCalculator.addMob(new ChunkPos(blockPos), mobCategory);
        }
	
	// 2.5 额外的生成数量限制
		mob.getMaxSpawnClusterSize() 
		/* 这种生物(MobCategory)的最大生成簇大小，并不是每组游走的限制，
			而是本区块这三组游走的数量之和的限制，因此到达上限就直接终止本区块这种生(mobCategory)的生成了
		*/
			Mob = 4，但是有覆写：
				桶装鱼和蝌蚪 = 8
				马类 = 6
				恶魂 = 1
				掠夺者 = 1
				狼 = 8
		mob.isMaxGroupSizeReached(p) // 目前只有热带鱼会触发这个限制
			mob = false
			热带鱼：有一套限制阻止同种类热带鱼生成超过一定数量

```
## 2.4 生物生成判断

### 2.4.1 刷怪过程中的生物生成判断
```java
		private static boolean isValidSpawnPostitionForType(
			ServerLevel serverLevel,
			MobCategory mobCategory,
			StructureManager structureManager,
			ChunkGenerator chunkGenerator,
			MobSpawnSettings.SpawnerData spawnerData,
			BlockPos.MutableBlockPos mutableBlockPos,
			double d
		) {
			EntityType<?> entityType = spawnerData.type();
			if (entityType.getCategory() == MobCategory.MISC) {
				return false;
			} else if (!entityType.canSpawnFarFromPlayer() && d > entityType.getCategory().getDespawnDistance() * entityType.getCategory().getDespawnDistance()) {
				return false;
			} else if (!entityType.canSummon() || !canSpawnMobAt(serverLevel, structureManager, chunkGenerator, mobCategory, spawnerData, mutableBlockPos)) { //canSpawnMobAt 
				return false; // canSummon()只有鱼钩浮标和玩家为false，可以忽略此项检查
			} else if (!SpawnPlacements.isSpawnPositionOk(entityType, serverLevel, mutableBlockPos)) { // SpawnPlacementsTypes相关的检查
				return false;
			} else {
				return !SpawnPlacements.checkSpawnRules(entityType, serverLevel, EntitySpawnReason.NATURAL, mutableBlockPos, serverLevel.random) // SpawnPredicate相关的检查
					? false
					: serverLevel.noCollision(entityType.getSpawnAABB(mutableBlockPos.getX() + 0.5, mutableBlockPos.getY(), mutableBlockPos.getZ() + 0.5)); // 检查生物的碰撞箱是否与其它方块的碰撞箱冲突
			}
		}

			public AABB getSpawnAABB(double d, double e, double f) {
				float g = this.spawnDimensionsScale * this.getWidth() / 2.0F;
				float h = this.spawnDimensionsScale * this.getHeight();
				return new AABB(d - g, e, f - g, d + g, e + h, f + g);
			}



		/** 返回true的条件是: 
				生成类型不是misc(杂项)
				&& (距离玩家<=生物的消失距离 || 能远离玩家生成(canSpawnFarFromPlayer))
				&& canSpawnMobAt
				&& 通过此生物的SpawnPlacements里的SpawnPlacementsTypes检查
				&& 通过此生物的SpawnPlacements里的SpawnPredicate的检查
				&& 生成的生物碰撞箱不会与**方块**的碰撞箱
		**/

		// 验证生物在新的位置是否依然可生成
		private static boolean isValidPositionForMob(ServerLevel serverLevel, Mob mob, double d) {
			return d > mob.getType().getCategory().getDespawnDistance() * mob.getType().getCategory().getDespawnDistance() && mob.removeWhenFarAway(d)
				? false
				: mob.checkSpawnRules(serverLevel, EntitySpawnReason.NATURAL) && mob.checkSpawnObstruction(serverLevel);
		}

		public boolean checkSpawnObstruction(LevelReader levelReader) {
			return !levelReader.containsAnyLiquid(this.getBoundingBox()) && levelReader.isUnobstructed(this);
		}

		/** 返回true的条件是:
				(距离玩家<=立即消失距离 || 不会远离玩家消失(removeWhenFarAway))
				&& 允许自然生成 
				&& 生物碰撞箱不在液体中 
				&& 生物碰撞箱没有被**实体**的碰撞箱阻塞
		**/
```
### 2.4.1 Mob.checkSpawnRules

注意：mob.checkSpawnRules 与 SpawnPlacements.checkSpawnRules 不是同一个东西

```java
// Mob类(直接返回true)：
    public boolean checkSpawnRules(LevelAccessor levelAccessor, EntitySpawnReason entitySpawnReason) {
        return true;
    }

	// 其中有且只有一个覆写(PathFinderMob类)(也是直接返回true)：
		public boolean checkSpawnRules(LevelAccessor levelAccessor, EntitySpawnReason entitySpawnReason) {
			return this.getWalkTargetValue(this.blockPosition(), levelAccessor) >= 0.0F;
		}

		// 下面研究所有寻路生物(PathFinderMob)的覆写(直接返回true)：
			public float getWalkTargetValue(BlockPos blockPos, LevelReader levelReader) {
				return 0.0F;
			}

		// 寻路类生物有一堆覆写，这里面终于有不是返回true的了
		// 这些覆写里面几乎总是涉及“计算光照造成的寻路代价”
			default float getPathfindingCostFromLightLevels(BlockPos blockPos) {
				return this.getLightLevelDependentMagicValue(blockPos) - 0.5F; // 光照幻数 - 0.5
			}
```
去翻阅我光照相关的分析，会发现这个“光照幻数”往往倍计算出来就是和0.5比较大小的
	实际亮度为11，光照幻数：主世界和末地≈0.4，下界≈0.44
	实际亮度为12，光照幻数：主世界和末地=0.5，下界=0.55
	实际亮度为13，光照幻数：主世界和末地≈0.6，下界≈0.66

下面列出所有的会让Mob.checkSpawnRules返回true条件：
```java
生物(Mob)：true
	寻路类生物(PathFinderMob)：true
		动物：下方是草方块 ? true : 实际光照 >= 12
			蘑菇牛：下方是菌丝 ? true : 实际光照 >= 12
			海龟：下方含水 || 下方是沙子 ? true : 实际光照 >= 12
			炽足兽：当前位置是岩浆 || 身体未接触到岩浆 ? true : false
			美西螈、蜜蜂：true
		怪物：实际亮度(主世界 <= 12, 下界 < 12)
			守卫者：下方含水 ? true : 实际亮度(主世界 <= 12, 下界 < 12)
			蠹虫：下方是可寄生方块 ? true : 实际亮度(主世界 <= 12, 下界 < 12)
			掠夺者、嘎吱怪、监守者、疣猪兽：true
```


### 2.4.3 生物放置条件(SpawnPlacements)

Mojang给每一种生物定义了生成条件，以下是完整代码，粗略看一眼即可：
```java
net.minecraft.world.entity.SpawnPlacements#checkSpawnRules

```
中间一大部分每种生物的生成条件，分为三部分：

1. HeightMapType(高度图类型)，仅在世界生成时生成“原住民”

2. SpawnPlacementTypes(on_ground, in_water等)，生物生成的粗略环境判断

3. SpawnPredicate(最后一项check某某SpawnRules)，生物生成的精细环境判断

```java
net.minecraft.world.entity.SpawnPlacementTypes
public interface SpawnPlacementTypes {
    SpawnPlacementType NO_RESTRICTIONS = (levelReader, blockPos, entityType) -> true;
    SpawnPlacementType IN_WATER = (levelReader, blockPos, entityType) -> {
        if (entityType != null && levelReader.getWorldBorder().isWithinBounds(blockPos)) {
            BlockPos blockPos2 = blockPos.above();
            return levelReader.getFluidState(blockPos).is(FluidTags.WATER) && !levelReader.getBlockState(blockPos2).isRedstoneConductor(levelReader, blockPos2);
        } else {
            return false;
        }
    };
    SpawnPlacementType IN_LAVA = (levelReader, blockPos, entityType) -> entityType != null && levelReader.getWorldBorder().isWithinBounds(blockPos)
        ? levelReader.getFluidState(blockPos).is(FluidTags.LAVA)
        : false;
    SpawnPlacementType ON_GROUND = new SpawnPlacementType() {
        @Override
        public boolean isSpawnPositionOk(LevelReader levelReader, BlockPos blockPos, @Nullable EntityType<?> entityType) {
            if (entityType != null && levelReader.getWorldBorder().isWithinBounds(blockPos)) {
                BlockPos blockPos2 = blockPos.above();
                BlockPos blockPos3 = blockPos.below();
                BlockState blockState = levelReader.getBlockState(blockPos3);
                return !blockState.isValidSpawn(levelReader, blockPos3, entityType)
                    ? false
                    : this.isValidEmptySpawnBlock(levelReader, blockPos, entityType) && this.isValidEmptySpawnBlock(levelReader, blockPos2, entityType);
            } else {
                return false;
            }
        }

        private boolean isValidEmptySpawnBlock(LevelReader levelReader, BlockPos blockPos, EntityType<?> entityType) {
            BlockState blockState = levelReader.getBlockState(blockPos);
            return NaturalSpawner.isValidEmptySpawnBlock(levelReader, blockPos, blockState, blockState.getFluidState(), entityType);
        }

        @Override
        public BlockPos adjustSpawnPosition(LevelReader levelReader, BlockPos blockPos) {
            BlockPos blockPos2 = blockPos.below();
            return levelReader.getBlockState(blockPos2).isPathfindable(PathComputationType.LAND) ? blockPos2 : blockPos;
        }
    };
}

    public static boolean isValidEmptySpawnBlock(
        BlockGetter blockGetter, BlockPos blockPos, BlockState blockState, FluidState fluidState, EntityType<?> entityType
    ) {
        if (blockState.isCollisionShapeFullBlock(blockGetter, blockPos)) {
            return false;
        } else if (blockState.isSignalSource()) {
            return false;
        } else if (!fluidState.isEmpty()) {
            return false;
        } else {
            return blockState.is(BlockTags.PREVENT_MOB_SPAWNING_INSIDE) ? false : !entityType.isBlockDangerous(blockState);
        }
    }
```
分析后总结：
1.	NO_RESTRICTIONS (无限制) = 无条件可以

2.	IN_WATER (水中) = 世界边境之内 && 此方块含水 && 上方不是红石导体

3.	IN_LAVA (岩浆中) = 世界边境之内 && 此方块含岩浆

4.	ON_GROUND (在地面) = 世界边境之内 
		&& 下方方块允许生成此生物(isValidSpawn)
		&& 此方块和上方方块两个位置都是合法的生成空位(isValidEmptySpawnBlock)

	其中 ON_GROUND (在地面) 的后两个判定：
	1. isValidSpawn (生物能否在这上面生成)：
			
			通用判定：方块上表面支撑形状完整 && 方块发光亮度 < 14
			特判(无视通用判定)：
				never (总是不能)：
					无法破坏方块：基岩、屏障、
					玻璃类：玻璃、染色玻璃、铜网、
					装饰类：活板门、紫颂花、脚手架(1.19.3+)
				always (总是能)：
					两个上表面碰撞箱不完整的：灵魂沙、泥巴、
					三个类光源方块：雕刻南瓜、南瓜灯、红石灯
				岩浆块：免疫火的所有生物(.fireImmune)
				树叶：豹猫和鹦鹉
				冰、霜冰：北极熊
	
	2. 	isValidEmptySpawnBlock：(生物能否在内部生成)

			碰撞箱不能为完整(!isCollisionShapeFullBlock)
			&& 不能是红石信号源(isSignalSource())
			&& 不能含有液体
			&& 不是含有阻止怪物在内部生成的标签(!BlockTags.PREVENT_MOB_SPAWNING_INSIDE)(目前只包含四种铁轨)
			&& 不是对于这个生物危险的方块(!entityType.isBlockDangerous)
		
			最后一项 isBlockDangerous，检查在这个方块里是否对于这个生物危险
			(某些生物免疫某些危险方块的伤害(.fireImmune和.immuneTo()))
				如果不是以下危险方块，什么生物都返回false(即不危险)
				如果是某个危险方块，此生物又是对应免疫的生物就返回false(即不危险)，不是免疫的生物就返回true(危险)。
					
					免疫组合有：
					1. 燃烧的方块(火、岩浆、岩浆块、点燃的营火、岩浆锅)：
						下界生物：烈焰人、恶魂、岩浆怪、炽足兽、凋灵骷髅、僵尸疣猪兽、僵尸猪灵、凋零
						特殊生物：恼鬼、坚守者、末影龙、潜影贝
						其他实体：药水效果云、末影水晶、TNT
					2. 甜浆果：狐狸
					3. 细雪：雪傀儡、北极熊、流浪者
					4. 凋灵玫瑰：凋灵、凋灵骷髅
					5. 仙人掌：(无)

### 2.4.3 自然生成总结
简化为以下伪代码：
```java
对于每个维度：
	对于每个“实体运算的”区块：(随机顺序)
		对每种未达到总量上限生物类型(MobCategory)：
			水平随机一个位置
			从维度最低处到最高费空气方块之间选一个点作为生成原点(HeightMap.WorldSurface 相关)
			如果这个生成原点方块不是红石导体：
				j = 三组游走总生成数量
				三组从原点出发的随机游走(互不干扰)：
					每组生成进行o次生成：
						x,z 随机偏移(randomInt(6)-randomInt(6))
						o = 随机1~4，仅作为默认数值，后面会根据选中的生物修改
						p = 0 (热带鱼相关的计数器)
						如果(1)：
							当前位置距离玩家>24.0 && 距离出生点>=24.0 
							&& (当前位置还在生成原点的区块 || 当前位置强加载)
						那么：
							如果还未决定生成生物，则在当前位置随机选取可生成的生物
							如果选取出来的为空，直接停止这组游走
							spawnData为选取到的生成生物的信息
							o = 随机取该生物生成次数(最少次数~最大次数)
							如果(2)：
								满足生成势能判断
								&& 生成类型不是 misc(杂项)
								&& (距离玩家 <= 生物的立即消失距离 || 能远离玩家生成(canSpawnFarFromPlayer))
								&& 此生物依然在新位置的可生成列表中(canSpawnMobAt)
								&& 通过此生物的SpawnPlacements.Types 检查 (on_ground, in_water, in_lava, no_restrictions)
								&& 通过此生物的SpawnPlacements.checkSpawnRules 的检查 (checkXxxSpawnRules)
								&& 生成的生物碰撞箱不会被其它**方块**的碰撞箱阻塞
							那么：
								在缓存中生成此生物，偏航角随机(随机旋转)，俯仰角0度(平视)
								如果(3)：
									(距离玩家 <= 生物的立即消失距离 || 不会远离玩家消失(removeWhenFarAway))
									&& Mob.checkSpawnRules 
									&& 生物碰撞箱不在液体中 
									&& 生物碰撞箱没有被**实体**的碰撞箱阻塞
								那么：
									调用该生物的 finalizeSpawn 完善生成
									j++, p++
									尝试添加生物的乘客或着坐骑
									
									afterSpawn更新刷怪势能列表和这种生物类型的存在数量列表
									如果 j >= MaxSpawnClusterSize ，终止本区块这种生物类型的成群生成
									如果 p 达到了相关的数量限制(热带鱼独享)，只终止这组游走
```

再根据社区多年的经验，可总结出一下：
1. 生成原点：
	如果最开始的生成位置是**红石导体**，那么这个区块的这种生物(MobCategory)就**结束啦！**

	你最好不要在刷怪的平面内(不是指的地板)有任何红石导体，例如常用的粘液块、普通方块，
	
	但是侦测器、活塞、红石块、蜜块这样子的不可能充能方块都是可以的，最多就是阻止生物的某个点生成

2. 游走距离：
	游走只发生在水平面，因此如果地形不平坦也会影响生成的效率
	游走通过两个0~5的随机数差值来决定，实际上类似三角分布，因此多次游走的后**更倾向于原点**的位置
	P(n) = (6-|n|)/36

3. 游走影响效率：
	for循环里，是先发生游走，再选择怪物，因此根据环境选择怪物是发生在第一次游走的位置的，由此有以下技巧:
	1. 由于大多数生物每次成组生成的数量为1~4次，在大范围内都可以生成，那么刷怪区域往外再扩建20个方块及以内，理论上都是可以增加生成概率。
	
		但是由于游走的概率是趋向于原点的，因为游走很远的概率极低，根据经验，游走不超过10m内已经是99%的情况了。

		而又因为游走的次数是生物成组生成的最小数量到最大数量的随机值，平均只有2次，所以扩建更多区域也不是很有必要。

		根据经验，我推荐无论是什么生物，都扩建5个方块即可，因为这样子情况下和建造20米的游走的最终的效率差距非常小。

	2. 如果想要生成的生物只在小范围内可以生成，例如史莱姆区块，那么只有5m以内的游走对于这种生物是有效的，因为如果原点在5m以外，那么进行一次游走是不能进入生成区域，因此无法随机到只有在小范围结构可以生成的生物，所以生成区域边界以外扩建只有5个方块及以内都是有效的。

4. 待补充

# 3. 自定义生成
