# INTEGRAL TimeSystem

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/80x15.png" /></a>


*INTEGRAL in time: time conversion and definition of time-range constructs*

* convert time between UTC to
* find time ranges and observation sets for selection of conditions

Examples:

```
$ curl https://www.astro.unige.ch/cdci/astrooda/dispatch-data/gw/timesystem/api/v1.0/scwlist/nrt/2019-10-11T11:11:11/2020-11-11T11:11:11?ra=161.2647&dec=-59.68443&radius=8&min_good_isgri=1000&return_columns=SWID,RA_SCX,DEC_SCX
```


```
$ curl https://www.astro.unige.ch/cdci/astrooda/dispatch-data/gw/timesystem/api/v1.0/scwlist/nrt/2019-10-11T11:11:11/2020-11-11T11:11:11?ra=161.2647&dec=-59.68443&radius=8&min_good_isgri=1000&return_columns=SWID,RA_SCX,DEC_SCX&return_index_version=yes
```

