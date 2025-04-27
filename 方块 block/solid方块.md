# 方块种类
## solid方块：
solid方块的定义如下：

```java
//通常判断一个方块使用如下函数(net.minecraft.world.level.block.state.BlockBehaviour.BlockStateBase#isSolid)
public boolean isSolid() {
    return this.legacySolid;
}

//其中(net.minecraft.world.level.block.state.BlockBehaviour.BlockStateBase#legacySolid)：
this.legacySolid = this.calculateSolid();

//这部分就是solid的方块的定义方式了(net.minecraft.world.level.block.state.BlockBehaviour.BlockStateBase#calculateSolid)：
private boolean calculateSolid() {
    if (this.owner.properties.forceSolidOn) {
        return true;
    } else if (this.owner.properties.forceSolidOff) {
        return false;
    } else if (this.cache == null) {
        return false;
    } else {
        VoxelShape voxelShape = this.cache.collisionShape;
        if (voxelShape.isEmpty()) {
            return false;
        } else {
            AABB aABB = voxelShape.bounds();
            return aABB.getSize() >= 0.7291666666666666 ? true : aABB.getYsize() >= 1.0;
        }
    }
}
```
直译上面的代码：
1. 首先确认该方块是否有关于solid的特判(forceSolidOn与forceSolidOff)；
2. 没有特判会进行通用判断：如果碰撞箱(collisionShape)为空，那么此方块是“非solid方块”；否则进行一些参数的比较。

上述参数比较判断比较莫名其妙，特判部分和碰撞箱是否为空的部分比较好理解，但是下面的getSize()与getYsize()部分就有点奇怪了，下面是这些函数的定义：
```java
//getSize()函数：
public double getSize() {
    double d = this.getXsize();
    double e = this.getYsize();
    double f = this.getZsize();
    return (d + e + f) / 3.0;
}

//getYsize()函数：
    public double getYsize() {
        return this.maxY - this.minY;
    }
//AABB()里的max坐标轴    
    public AABB(double d, double e, double f, double g, double h, double i) {
        this.minX = Math.min(d, g);
        this.minY = Math.min(e, h);
        this.minZ = Math.min(f, i);
        this.maxX = Math.max(d, g);
        this.maxY = Math.max(e, h);
        this.maxZ = Math.max(f, i);
    }
```
由此我们可以看到，实际上getSize()作用就是获取了一个方块碰撞箱的最小外接长方体(最小能容纳下这个方块的摆正的长方体)，并求出了这个最小外接长方体的三维大小(单位：米)的平均数，然后用这个与这个特殊的常数0.7291666...做比较。
我们可以对这个式子做一下变形，就变成了：
(x,y,z分别为最小外接长方体的长、宽、高)
X+Y+Z >= 3 * 0.7291666666666666
注意到这个无限小数应该是35/48，上述式子化简为：
X+Y+Z >= 35/16
注意到分数分母为16，二此时的单位是米(m)，这启发我们用像素(px)作为单位去掉分母16，有：
X+Y+Z >= 35px = 16*2+3 (px)

这样子我门理解了这一步的目的：
1. 一个方块的碰撞箱的最小外接长方体，其长、宽、高之和**大于或等于35px**，那么这个方块就**是solid方块**;
2. 如果三维之和小于35px，即使最小外接长方体的高大于等于1也**仍然是solid方块**;
3. 否则若以上两项**都小于**，那就是**非solid方块**。

这样我们理解了soild除了特判，能满足solid的条件就是碰撞箱的最小外接长方体的长、宽、高之和大于等于35px，或着高大于等于1米，这两个任意满足一个都是solid方块；非solid方块就是除了这两个条件都不满足，或着是无碰撞箱的方块。

注意到三维之和判断的临界条件35px又等于2m+3px，看到“+3px”的部分，我联想到活板门的高度正好是3px，也就是活板门的三维之和为32+3=35px，所以活板门**是**solid方块，这是一个擦线过判定的例子。
而比较悲惨的就是比较器和中继器只有2px高，经过计算长宽高之和为32+2=34px，一像素之差小于35px，所以两个二极管原件**不是**solid方块。

有些方块例如玻璃板长宽只有2px，高度1m=16px，求和发现为20px < 35px，但是不只是玻璃板，包括各种栅栏，栅栏门依然是solid，这是因为他们都是被特判的，强制为solid方块。
经过翻阅代码，有
被强制设置为solid的(forceSolidOn)方块有：
移动中的方块
栅栏、栅栏门、石墙、玻璃/铁栅栏/铁链、压力板、旗帜、告示牌，
蜘蛛网、灯笼、紫水晶、幽匿类、滴水石锥、蛋糕、海龟蛋、潮涌核心、避雷针、竹子和竹笋、铃铛、紫水晶。

少部分方块(截止1.21只有8种)被强制为非soild方块(forceSolidOff)：
梯子，(任意层数)雪片，末地烛、紫颂植物、紫颂花、杜鹃花、盛开的杜鹃花、大型垂滴叶。

但是这还不足以让我们对solid方块有足够的了解，我们还需要知道solid方块被用于什么情况下的判断。经过查找isSolid函数被引用的位置，主要有：
1. 告示牌、旗帜、蜡烛、蛋糕、展示框等这类方块只能**放置在solid方块**上；
2. solid方块在耕地和土径上方会破坏这两种方块使之变成泥土，也会破坏仙人掌；
3. 在生物寻路中有多处涉及，例如怪物寻路时通常只能**穿过非solid方块**，怪物只能**生成在非solid方块**里；
4. 地面上凸起的solid方块能**阻挡**传送门生成；
5. 水流侧面**非solid**的方块的时候，渲染出来的那一侧的水位高度会比solid方块或同样流体时有所**降低**；当流体的斜下角有相同流体时，那如果这个流体的侧面是非solid方块，可以让流体产生朝这个侧面的流动(流体认为侧面的方块无法阻挡流体)；
6. 非常重要的一点，阻挡运动(blockMotion)的方块的判断依据:
    ```java
    //(net.minecraft.world.level.block.state.BlockBehaviour.BlockStateBase#blocksMotion)
    public boolean blocksMotion() {
        Block block = this.getBlock();
        return block != Blocks.COBWEB && block != Blocks.BAMBOO_SAPLING && this.isSolid();
    }
    ```
    阻挡运动的方块(blockMotion)等于除了竹笋和蜘蛛网以外的所有solid方块。这也就是说**solid方块**除了两个特例都是**阻挡运动**的方块，**非solid方块**是**不能阻挡运动**的方块。

在这个网站中可以看到那些为solid方块，哪些不是：
https://joakimthorsen.github.io/MCPropertyEncyclopedia/?selection=solid,blocks_motion#

注意到，绝大多数非solid方块都是些活的植物，软的或小的东西(按钮、中继器和比较器、特别是部分需要依靠的红石原件)，或者是流体与空气，传送门这类易碎物品。
soild方块都是固体的，感官上是硬的不易大幅度变形的，有大的碰撞体积，能支撑其余的方块，特别是例如各种木制品。其中一个值得注意的案例是活珊瑚是非soild，而死珊瑚就是solid方块。

综上所述，我认为solid方块代表的是一类硬的方块，能支撑住其他方块和实体，实体水流等能被阻挡影响的方块。而非soild方块大多是活的软的容易变形的植物，空气与流体，各种传送门等虚的东西，或是一些需要依赖的易碎品(一些红石原件，装饰物，脚手架)

Wiki给solid方块的翻译为“固体方块”，这是一种非常不准确的翻译与说法，因为mc里几乎除了空气与流体，所有方块都是固体形态的。

我认为非solid方块最佳的翻译为“软弱方块”，而solid方块翻译为“坚硬方块”“坚固方块”“坚实方块”等更为合理。

solid方块是有明确定义的概念中一个非常容易被忽视与误解的方块，不仅来自于混乱的翻译，也来自于mojang定义的模糊抽象，大部分方块不是通过特判而是通过简简单单的计算三围尺寸就一刀切，造成了很多误解，例如对告示牌能放置的方块产生疑惑，上方有什么样的方块能阻止下方的水源结冰与方块上积雪等。但是solid方块的概念对技术mc玩家的重要程度仅次于红石导体，所以我认为有必要对solid方块进行详细解释，我的第一个mc的知识讲解就是这个solid方块的定义，而不是看起来更重要的红石导体(RedstoneConductor)，希望对大家更深的理解mc有所帮助。

非solid方块的用法：
1. 在一个水流的侧面放一个非solid方块，这个非solid方块下面如果是有水的(包括含水方块)，顶上的水流会向侧面流动，不过要注意水流的方向不是水流的状态，是渲染的，也是实体实时计算的，侦测器无法感知水流的方向，水流只有水位高度(level)这一个状态。