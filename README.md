# New version available and this repo will be read only.

Please see the new repo here: https://github.com/derekhe/msfs2020-google-map-electron

# [English version here](./README.EN.md)

# 中文
## 免责声明

本教程提到的方法仅用于研究和学习用途。我不对使用、拓展该教程及方法所造成的任何法律责任和损失负责。

## 原理

替换本地的DNS，将微软服务器替换成本地服务器并从google地图上获取到卫星图像返回给游戏。涉及到的工具，请自行安装
* 一个可以访问Google的HTTP代理（如果你在墙外可以直接访问，可忽略）

## 有哪些增强

* 对地表的卫星图片进行全局替换成谷歌的
* 有些地方bing地图没有数据会被显示成自动生成的卫星图，非常丑。谷歌地图涵盖地球所有的地方，不会出现这种问题。
* 谷歌地图的卫星图比Bing地图更新更快
* 游戏中微软做了个颜色修正，导致地图偏色很严重（常见偏色是绿色，特别是很多地方卫星图不好的地方），我将这个功能去掉，返回原来本来的颜色。

## 什么做不到
* 自动生成的建筑、树木、道路和之前是一样的。
* 倾斜摄影生成的建筑还是和之前一样，不会用谷歌替换

## 使用步骤

注意：如果杀毒软件报错，请加入白名单，都是误报；如果报告证书错误，请直接同意，否则加载不出来。

请参考：https://www.bilibili.com/video/BV1Eh411t7on/

## 背景

微软模拟飞行2020的地景使用了Bing的卫星地图，然而卫星地图比较老旧，很多地区都是几年前的图设置直接是没有的。这种现象在全球不同地区都有。在大陆的图更是10年前的图，有大量地区的卫星图都是没有的，微软便使用程序生成的图代替，质量非常的差。替换过后画质和细节得以明显的提升，可以见下图

## 原始地图
![原始地图](./doc/compare-1.jpg)

## Google地图替换后可以得到高清最新的影像

### 一个小城镇
![一个小城镇](./doc/compare-2.jpg)
![一个小城镇](./doc/compare-3.png)

### 青海湖（这些卫星图在Bing中不存在）

![青海湖](./doc/lake.jpg)
![青海湖](./doc/lake-2.jpg)
![青海湖](./doc/lake-3.jpg)

### 成都

![成都](./doc/chengdu.png)

### 香港

![香港](./doc/hongkong.jpg)


## 历史及相关资料

我很早就在研究用谷歌地图替换的可能性，在网上也有油管大神提供了[一些思路](https://flightsim.to/file/4074/google-earth-decoder-optimisation-tools?__cf_chl_jschl_tk__=pmd_2902fb008a3441de2f812b093625596ad796f737-1628304162-0-gqNtZGzNAk2jcnBszQjO)，使用爬虫从谷歌爬下数据然后导入到MSFS2020中。但这种方式比较复杂，不能大规模的使用。

后来我研究了下网络请求，发现MSFS会从bing的服务器上下载图片，理论上讲将图片替换成另外的图片应该是可以的。而且恰好bing和google的卫星图片的切片方式是类似的可以进行无缝切换，甚至微软还提供了转换的[源代码]（https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system）（见QuadKeyToTileXY这个函数）

在不断的搜索过程中，发现了[和我思路类似的例子](
https://github.com/muumimorko/MSFS2020_CGLTools/issues/2#issuecomment-762232597)。但他的主要目的是将一些不要的东西去掉以改善地景质量。他还建立了一个另外的仓库用来演示一个[使用代理方式替换地景的方法]（https://github.com/muumimorko/MSFS2020_Proxy）。遗憾的是这个仓库缺少一些必要的东西，无法正常的运行。

![IMG](https://user-images.githubusercontent.com/9518369/104909810-173dfb00-5991-11eb-8e17-4063deb7ab8f.jpg)

# 赞助

如果你已经成功的实现了，请给个star，让更多人看到！
如果你愿意给与作者一些赞助，请扫描以下二维码支持一下作者。

![微信](./doc/mm_reward_qrcode_1628320842310.png)
![阿里](./doc/1628320893.jpg)
