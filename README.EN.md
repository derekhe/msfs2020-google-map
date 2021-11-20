# English version

## Disclaimer

The methods mentioned in this tutorial are for research and learning purposes only. I am not responsible for any legal liabilities and losses caused by using or expanding this tutorial and method.

## Important
ALWAYS checkout latest version here first if you have trouble: https://github.com/derekhe/msfs2020-google-map/releases

**!!!!!MUST DO BEFORE YOU USE THIS MOD!!!!!**

PLEASE VIEW THE VIDEO FOR INSTALLATION AND USAGE: https://youtu.be/Lk7GK5XLTt8

SweViver made this great comparsion and installation here: https://www.youtube.com/watch?v=E11XsrBdzcg

**Some people use cracked verison of MSFS, please don't use this mod, it is not supported.

If you have any problem, please watch the videoes first and look at this FAQ page: https://github.com/derekhe/msfs2020-google-map/wiki/FAQ

## Donate
I will keep this mod up to date for every MSFS update as much as I can. If you like this plugin and want to offer me a coffee, please click the "DONATE ME A COFFEE" button, or here is the link: https://paypal.me/siconghe?country.x=C2&locale.x=en_US

Thanks for your support! 

## background

Microsoft Flight Simulator 2020 uses Bing's satellite map. However, the satellite map is relatively old, and many areas are not directly equipped with map settings a few years ago. This phenomenon occurs in different regions of the world. The map on the mainland is even 10 years ago. There are a large number of regions where satellite images are not available. Microsoft uses the program-generated map instead, and the quality is very poor. After the replacement, the image quality and details have been significantly improved, as shown in the figure below

## Original map
![Original map](./doc/compare-1.jpg)

## You can get the latest high-definition images after replacing Google Maps

### A small town
![A small town](./doc/compare-2.jpg)
![A small town](./doc/compare-3.png)

### Qinghai Lake (These satellite images do not exist in Bing)

![Qinghai Lake](./doc/lake.jpg)
![Qinghai Lake](./doc/lake-2.jpg)
![Qinghai Lake](./doc/lake-3.jpg)

### Chengdu

![Chengdu](./doc/chengdu.png)

### Hong Kong

![Hong Kong](./doc/hongkong.jpg)


## History and related information

I have been studying the possibility of replacing it with Google Maps for a long time, and there are also YouTubers on the Internet who have provided [some ideas](https://flightsim.to/file/4074/google-earth-decoder-optimisation-tools?__cf_chl_jschl_tk__= pmd_2902fb008a3441de2f812b093625596ad796f737-1628304162-0-gqNtZGzNAk2jcnBszQjO), use a crawler to crawl the data from Google and import it into MSFS2020. But this method is more complicated and cannot be used on a large scale.

Later I studied the network request and found that MSFS will download pictures from Bing's server. In theory, it should be possible to replace the pictures with other pictures. And it happens that the slicing method of bing and google’s satellite images is similar and can be seamlessly switched, and even Microsoft also provides the converted [source code] (https://docs.microsoft.com/en-us/bingmaps/articles/ bing-maps-tile-system) (see this function QuadKeyToTileXY)

In the process of constant search, I found [examples similar to my thinking](
https://github.com/muumimorko/MSFS2020_CGLTools/issues/2#issuecomment-762232597). But his main purpose is to remove some unnecessary things to improve the quality of the landscape. He also built an additional warehouse to demonstrate a [method of using proxy to replace landscape] (https://github.com/muumimorko/MSFS2020_Proxy). Unfortunately, this warehouse lacks some necessary things and cannot operate normally.

![IMG](https://user-images.githubusercontent.com/9518369/104909810-173dfb00-5991-11eb-8e17-4063deb7ab8f.jpg)
