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
				Util.shuffle(list, this.level.random);
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
		boolean bl2 = this.level.getLevelData().getGameTime() % 400L == 0L; // 每隔400tick bl2值才会变成一次true，用于定期触发生成持久不消失的生物("creature"(动物))
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
2. 遍历所有需要运算的区块：自然生成(NaturalSpawn)和区块刻
3. 每个维度的自定义生成(CustomSpawn)

我们首先关注自然生成(NaturalSpawn)：

在此之前我门需要首先了Mojang划分的生物种类(MobCategory)有哪些：
```java
public enum MobCategory implements StringRepresentable {
    MONSTER("monster", 70, false, false, 128),
    CREATURE("creature", 10, true, true, 128),
    AMBIENT("ambient", 15, true, false, 128),
    AXOLOTLS("axolotls", 5, true, false, 128),
    UNDERGROUND_WATER_CREATURE("underground_water_creature", 5, true, false, 128),
    WATER_CREATURE("water_creature", 5, true, false, 128),
    WATER_AMBIENT("water_ambient", 20, true, false, 64),
    MISC("misc", -1, true, true, 128);

    public static final Codec<MobCategory> CODEC = StringRepresentable.fromEnum(MobCategory::values);
    private final int max;
    private final boolean isFriendly;
    private final boolean isPersistent;
    private final String name;
    private final int noDespawnDistance = 32;
    private final int despawnDistance;

    private MobCategory(final String string, final int i, final boolean bl, final boolean bl2, final int j) {
        this.name = string;
        this.max = i;
        this.isFriendly = bl;
        this.isPersistent = bl2;
        this.despawnDistance = j;
    }
}
```
整理后:

| Name                       | 名字                     | 上限 | 持久   | 消失距离 | 友好   |
| :--------------------------| :----------------------- |:-----|:------|:------|:------|
| monster                    | 怪物                     | 70   | false  | 128     | false  |
| creature                   | 动物                     | 10   | true   | 128     | true   |
| ambient                    | 环境(蝙蝠)               | 15   | false  | 128     | true   |
| water_ambient              | 水生环境(桶装鱼)          | 20   | false  | 64      | true   |
| water_creature             | 水生生物(鱿鱼、海豚)     | 5    | false  | 128     | true   |
| underground_water_creature | 地下水生生物(发光鱿鱼)   | 5    | false  | 128     | true   |
| axolotls                   | 美西螈                   | 5    | false  | 128     | true   |
| misc                       | 杂项                     | -1   | true   | 128     | true   |

1. 其中杂项(misc)类似于Others，不参与自然生成。
2. 友好(isFriendly)表示是否为友好生物
3. 持久(isPersistent)表示是否为持久存在不消失的生物
4. 消失距离(despawnDistance)表示距离最近玩家超过这个距离就会立即消失
5. 不消失距离(noDespawnDistance)表示距离最近玩家超过这个距离就会开始消失，有玩家在这个范围内则不会。
5. 上限(max)表示单玩家附近最大的生物数量



# 关于Mob类生物消失(despawn)：
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
大致意思就是：
1. 如果难度为和平模式，并且生物需要消失(shouldDespawnInPeaceful)，则直接消失。
	shouldDespawnInPeaceful()方法：
	怪物(Monster)：true
	恶魂，幻翼，史莱姆(size > 0)：true
	猪灵：false
	其它：false
2. 如果生物因为各种原因带上了(setPersistenceRequired)持久属性，则不会消失，且noActionTime设置为0。
3. 如果没有阻止消失的属性，则距离最近玩家距离d>128，且满足过远消失条件(removeWhenFarAway(d))，则生物消失。
	removeWhenFarAway(d)方法：d为距离最近玩家距离，一般情况下返回false，特判较多：
		// false类
		动物：return false
		傀儡类：return false
		悦灵：return false
		
		// 条件类
		鸡：return this.isChickenJockey()
		猫：return !this.isTame() && this.tickCount > 2400
		豹猫：return !this.isTrusting() && this.tickCount > 2400
		桶装鱼和美西螈：return !this.fromBucket() && !this.hasCustomName()
		僵尸村民：return !this.isConverting() && this.villagerXp == 0
		
		// 前面不是判断过了吗，这里为啥梅开二度？
		疣猪兽：return !this.isPersistenceRequired()
		猪灵：return !this.isPersistenceRequired()
		坚守者：return !this.isPersistenceRequired()
		
		// 正在参加袭击的和灾厄巡逻队不会消失
		灾厄巡逻队：return !this.patrolling || d > 16384.0 // d表示距离最近玩家距离
			袭击队伍：return this.getCurrentRaid() == null ? super.removeWhenFarAway(d) : false
4. 如果没有阻止消失的属性，则距离最近玩家距离d>32，且满足过远消失条件(removeWhenFarAway(d))，
	那么noActionTime>600时，有1/800的概率消失(期望40s，半衰期log(0.5, 1-1/800)≈27.7)。
	否则如果距离最近玩家距离d<32，noActionTime重置为0。
5. 上文反复提及的noActionTime，表示生物在最近玩家距离内没有动作的时间，用于判断生物是否消失。
	生物会因为各种行为甚至是受伤让noActionTime重置为0，否则每tick增加1或2(怪物在特定光照下)。
6. 凋灵在和平模式而消失，否则非和平模式noActionTime设置为0；末影龙不会消失；潜影贝的子弹在和平模式也会消失。
