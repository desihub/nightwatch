# Nightwatch change log

## 0.3.3 (unreleased)

* Remove job throttling at KPNO so that the Nightwatch monitor attempts to allocate 30 jobs for preproc/qproc.
* Added script to correlated calibration standards with local conditions (temperature, pressure, humidity, ...).
* Updated KPNO hostname to desi-8.
* Updated DARK and READNOISE thresholds.
* Fixed broken check for device type in positioner loop plots.
* Added preproc and qproc --fallback-on-dark-not-found
  ([PR #380](https://github.com/desihub/nightwatch/pull/380)), required by
  [desispec PR #2162](https://github.com/desihub/desispec/pull/2162). 

## 0.3.2 (2023-03-20)

* Added placeholder pages for spectro QA in ZERO and DARK exposures ([PR #338](https://github.com/desihub/nightwatch/pull/338))
* Updated logo using DALL-E 2.

## 0.3.1 (2023-01-21)

* Updated flat standard thresholds ([PR #332](https://github.com/desihub/nightwatch/pull/332))

## 0.3.0 (2023-01-14)

### Major Updates

* Added calibration standards for ARCS and FLATS: PRs [#326](https://github.com/desihub/nightwatch/pull/326), [#328](https://github.com/desihub/nightwatch/pull/328), [#329](https://github.com/desihub/nightwatch/pull/329).
  - Standards defined for integrated flux (FLATS) and areas of bright lines (ARCS) in JSON format.
  - New `calibrations` module to load JSON standards for any given cal program.
  - Arc/flat cal info stored in `PER_SPECTRO` QA data structures.
  - Include plots of arc line areas and integrated fluxes to `qa-spectro*.html` pages.
  - Added of `PER_SPECTRO` exposure status to the top-level exposure table.
  - Removed disused fiber and spectro QA menu links.
  - Created static spectra QA page similar to the QA pages for amps and cameras.
* User interface improvements:
  - Classify spectra using `DESI_MASK` rather than `OBJTYPE`, useful with science targets. See PRs [#323](https://github.com/desihub/nightwatch/pull/323), [#325](https://github.com/desihub/nightwatch/pull/325).
  - Enable taptool to link to target images on [Legacy Survey Viewer](https://www.legacysurvey.org/viewer-desi) ([PR #309](https://github.com/desihub/nightwatch/pull/309)).
  - Move camfiber plots into tabs for faster and easier comparisons ([PR #302](https://github.com/desihub/nightwatch/pull/302)).
* Fixed broken assembly of fibermaps at KPNO: PRs [#313](https://github.com/desihub/nightwatch/pull/313), [#317](https://github.com/desihub/nightwatch/pull/317), [#318](https://github.com/desihub/nightwatch/pull/318).

### Minor Updates

* Highlight bright unmasked pixels in DARKs ([PR #316](https://github.com/desihub/nightwatch/pull/316)).
* Adjusted thresholds:
  - Z5 readnoise correction ([PR #305](https://github.com/desihub/nightwatch/pull/305)).
* Cosmetic improvements to plots and tables:
  - Added spectrograph labels to CCD QA index page ([PR #312](https://github.com/desihub/nightwatch/pull/312)).
  - Fixed broken downsampling form due to unclosed anchor tag ([PR #308](https://github.com/desihub/nightwatch/pull/308)).
  - Fixed squashed focalplane plots in Safari ([PR #303](https://github.com/desihub/nightwatch/pull/303)).
  - Color updates with labels for spectra ([PR #294](https://github.com/desihub/nightwatch/pull/294)).
  - Fixed broken SurveyQA link in exposure tables ([PR #311](https://github.com/desihub/nightwatch/pull/311)).
  - Dead SurveyQA link pointed to Survey-Ops nightqa page ([PR #293](https://github.com/desihub/nightwatch/pull/293)).
* Documentation:
  - Fixes to help tool links on several plots: PRs [#292](https://github.com/desihub/nightwatch/pull/292), [#295](https://github.com/desihub/nightwatch/pull/295), [#299](https://github.com/desihub/nightwatch/pull/299), [#300](https://github.com/desihub/nightwatch/pull/300).
  - Modified instructions for updating Nightwatch on `cori` and `perlmutter` ([PR #306](https://github.com/desihub/nightwatch/pull/306)).
* Fixes to enable Nightwatch processing in OS X:
  - Fix pandas "chained index" that caused mislabeling of disabled fibers ([PR #297](https://github.com/desihub/nightwatch/pull/297)).
  - Avoid recursive subprocess creation ([PR #296](https://github.com/desihub/nightwatch/pull/296)).

## 0.2.0 (2022-08-19)

### Major updates

* User interface improvements:
  - Redirect HelpTool links to Nightwatch wiki for most plots. (PRs [#268](https://github.com/desihub/nightwatch/pull/268), [#269](https://github.com/desihub/nightwatch/pull/269))
  - Fix prev/next links table and plot pages. (PRs [#227](https://github.com/desihub/nightwatch/pull/227), [#282](https://github.com/desihub/nightwatch/pull/282))
  - Add gridplot of CCD images for fast QA (PRs [#275](https://github.com/desihub/nightwatch/pull/275), [#278](https://github.com/desihub/nightwatch/pull/278))
  - Add overlay of masked pixels to CCD images. ([PR #272](https://github.com/desihub/nightwatch/pull/272))
  - Include image masks in amplifier QA ([PR #243](https://github.com/desihub/nightwatch/pull/243))
  - Improved camfiber and positioning plots ([PR #225](https://github.com/desihub/nightwatch/pull/225), [#232](https://github.com/desihub/nightwatch/pull/232))
  - Spectra plots default to calibrated versions ([PR #212](https://github.com/desihub/nightwatch/pull/212))
  - Added more info to exposures list ([PR #205](https://github.com/desihub/nightwatch/pull/205))
  - Added placeholder HTMLs for missing plots to avoid `ERROR not found` in links ([PR #164](https://github.com/desihub/nightwatch/pull/164))
  - Added `surveyqa` processing and links ([PR #153](https://github.com/desihub/nightwatch/pull/153))
  - Added guide plots page to nightwatch ([PR #151](https://github.com/desihub/nightwatch/pull/151))
  - Added fibers-on-target and positioner accuracy plots ([PR #150](https://github.com/desihub/nightwatch/pull/150))
* Backend processing:
  - Simplify CPU allocation at NERSC, KPNO, laptops ([PR #285](https://github.com/desihub/nightwatch/pull/285))
  - Creation of fibermaps during exposure processing ([PR #253](https://github.com/desihub/nightwatch/pull/253))
  - Support 2-amp readout ([PR #233](https://github.com/desihub/nightwatch/pull/233))
  - Make calendar writing faster ([PR #184](https://github.com/desihub/nightwatch/pull/184))
  - Updated batch processing to include plots, stop using `/tmp` ([PR #177](https://github.com/desihub/nightwatch/pull/177))
  - Improved parallelization in preproc, amps, noise, SNR calculations (PRs [#154](https://github.com/desihub/nightwatch/pull/154), [#159](https://github.com/desihub/nightwatch/pull/159), [#161](https://github.com/desihub/nightwatch/pull/161), [#167](https://github.com/desihub/nightwatch/pull/167))
  - Addressed vulnerability on spin (PRs [#170](https://github.com/desihub/nightwatch/pull/170), [#171](https://github.com/desihub/nightwatch/pull/171), [#172](https://github.com/desihub/nightwatch/pull/172))
  - Avoid NERSC I/O slowdowns by writing to temporary directory ([PR #166](https://github.com/desihub/nightwatch/pull/166))
  - Incorporated updates to logging and `fitsio` for use at NERSC ([PR #148](https://github.com/desihub/nightwatch/pull/148))
  - Update exposures table only for current night ([PR #130](https://github.com/desihub/nightwatch/pull/130))

### Minor updates

* Warning and error level adjustments:
  - READNOISE thresholds (PRs [#217](https://github.com/desihub/nightwatch/pull/217), [#229](https://github.com/desihub/nightwatch/pull/229), [#233](https://github.com/desihub/nightwatch/pull/233), [#245](https://github.com/desihub/nightwatch/pull/245), [#254](https://github.com/desihub/nightwatch/pull/254), [#274](https://github.com/desihub/nightwatch/pull/274)).
  - COSMIC RATE thresholds (PRs [#240](https://github.com/desihub/nightwatch/pull/240), [#254](https://github.com/desihub/nightwatch/pull/254), [#267](https://github.com/desihub/nightwatch/pull/267), [#290](https://github.com/desihub/nightwatch/pull/290)).
  - ZERO + DARK thresholds (PRs [#231](https://github.com/desihub/nightwatch/pull/231), [#236](https://github.com/desihub/nightwatch/pull/236)).
  - TRACESHIFT thresholds (PRs [#251](https://github.com/desihub/nightwatch/pull/251), [#256](https://github.com/desihub/nightwatch/pull/256)).
* Documentation:
  - Added links to update instructions ([PR #266](https://github.com/desihub/nightwatch/pull/266))
  - Added README with testing instructions at NERSC (PRs [#246](https://github.com/desihub/nightwatch/pull/246), [#247](https://github.com/desihub/nightwatch/pull/247), [#248](https://github.com/desihub/nightwatch/pull/248))
  - Added docs for updating docker on rancher 2 ([PR #174](https://github.com/desihub/nightwatch/pull/174))
* Bug fixes:
  - Fixed a bug in reporting qproc fails for the summary tables ([PR #262](https://github.com/desihub/nightwatch/pull/262))
  - Fixed fibers-on-target scale problems ([PR #250](https://github.com/desihub/nightwatch/pull/250))
  - Environment variable guard check to avoid crashes at KPNO ([PR #244](https://github.com/desihub/nightwatch/pull/244))
  - Handle `NIGHT=None` cases in exposure header ([PR #215](https://github.com/desihub/nightwatch/pull/215))
  - Plot robustness ([PR #187](https://github.com/desihub/nightwatch/pull/187)); handle coordinates files with and without FIBER column ([PR #189](https://github.com/desihub/nightwatch/pull/189))
  - Corrected random spectra selection and plotting ([PR #181](https://github.com/desihub/nightwatch/pull/181))
  - Bytestr/str fixes for pandas and bokeh 2.2 ([PR #178](https://github.com/desihub/nightwatch/pull/178))
  - Improved focal plane plot color scaling ([PR #176](https://github.com/desihub/nightwatch/pull/176))
  - Fixed compatibility issues with `fitsio` ([PR #168](https://github.com/desihub/nightwatch/pull/168))
  - Fixed incorrect handling of `qproc` errors ([PR #165](https://github.com/desihub/nightwatch/pull/165))
  - Fixed amp axis labels ([PR #158](https://github.com/desihub/nightwatch/pull/158))
  - Handle errors due to missing guide-rois (PRs [#155](https://github.com/desihub/nightwatch/pull/155), [#157](https://github.com/desihub/nightwatch/pull/157))
  - Fixed spectra plotting with mismatched fibermaps ([PR #129](https://github.com/desihub/nightwatch/pull/129))
  - Updated to new `OBSTYPE` keyword instead of `FLAVOR` ([PR #126](https://github.com/desihub/nightwatch/pull/126))
* Cosmetic updates:
  - Made docker directory neater/easier to pull and use without much modification ([PR #173](https://github.com/desihub/nightwatch/pull/173))
  - Blank pixels filled in rotated guide images ([PR #163](https://github.com/desihub/nightwatch/pull/163))

## 0.1.0 (2019-10-02)

Initial release for DESI Commissioning.

### Major updates

* User interface changes and improvements:
  - Renamed `qqa` to `nightwatch` ([PR #119](https://github.com/desihub/nightwatch/pull/119))
  - Indicated failed processing in exposures table ([PR #108](https://github.com/desihub/nightwatch/pull/108))
  - Added logfile viewing capabilities ([PR #91](https://github.com/desihub/nightwatch/pull/91))
  - Added `PER_SPECTRO` metadata column to exposures table ([PR #90](https://github.com/desihub/nightwatch/pull/90))
  - Added navigation tools for spectra accessed through flask ([PR #79](https://github.com/desihub/nightwatch/pull/79))
  - Used taptool to open spectra plots from left-clicking on camfiber plots ([PR #73](https://github.com/desihub/nightwatch/pull/73))
  - Added user options to plot raw or calibrated QA data ([PR #68](https://github.com/desihub/nightwatch/pull/68))
  - Added exptime to exposures table ([PR #51](https://github.com/desihub/nightwatch/pull/51))
  - Added spectra plots to flask app, showing by spectrograph and by `OBJTYPE` ([PR #48](https://github.com/desihub/nightwatch/pull/48))
  - Interface cleanup: new nav bar, dropdown menus, consistent colors, labels ([PR #43](https://github.com/desihub/nightwatch/pull/43))
  - Added camera QA pages and `PER_CAMERA` QA data, such as trace shifts (PRs [#9](https://github.com/desihub/nightwatch/pull/9), [#24](https://github.com/desihub/nightwatch/pull/24))
  - Added `preproc` CCD image and `PER_AMP` QA (PRs [#4](https://github.com/desihub/nightwatch/pull/4), [#6](https://github.com/desihub/nightwatch/pull/6), [#8](https://github.com/desihub/nightwatch/pull/8), [#23](https://github.com/desihub/nightwatch/pull/23))
  - Added `PER_CAMFIBER` QA (PRs [#10](https://github.com/desihub/nightwatch/pull/10), [#12](https://github.com/desihub/nightwatch/pull/12), [#20](https://github.com/desihub/nightwatch/pull/20), [#22](https://github.com/desihub/nightwatch/pull/22))
  - Set up calendar with processed nights and exposure QA tables (PRs [#1](https://github.com/desihub/nightwatch/pull/1), [#2](https://github.com/desihub/nightwatch/pull/2), [#3](https://github.com/desihub/nightwatch/pull/3))
* Backend and processing:
  - Renamed `bin/qqa_web_app.py` to `py/nightwatch/webapp.py` ([PR #120](https://github.com/desihub/nightwatch/pull/120))
  - Added docker configuration files ([PR #112](https://github.com/desihub/nightwatch/pull/112))
  - Switched over from fitsio to astropy ([PR #111](https://github.com/desihub/nightwatch/pull/111))
  - Improved logging of `qproc` status (PRs [#100](https://github.com/desihub/nightwatch/pull/100), [#101](https://github.com/desihub/nightwatch/pull/101))
  - Set timeseries processing (PRs [#13](https://github.com/desihub/nightwatch/pull/13), [#15](https://github.com/desihub/nightwatch/pull/15), [#16](https://github.com/desihub/nightwatch/pull/16), [#17](https://github.com/desihub/nightwatch/pull/17), [#98](https://github.com/desihub/nightwatch/pull/98))
  - Enable skipping of exposures without generated QA files ([PR #96](https://github.com/desihub/nightwatch/pull/96))
  - Improved robustness against empty folders and/or failed processing (PRs [#78](https://github.com/desihub/nightwatch/pull/78), [#92](https://github.com/desihub/nightwatch/pull/92))
  - Added `startdate` to monitor processing ([PR #88](https://github.com/desihub/nightwatch/pull/88))
  - Closed/joined pools in `run.py` ([PR #72](https://github.com/desihub/nightwatch/pull/72))
  - Added scripts to generate READNOISE, ZERO+DARKS, and COSMIC thresholds ([PR #70](https://github.com/desihub/nightwatch/pull/70))
  - Enabled auto-updating of latest exposure summary (PRs [#52](https://github.com/desihub/nightwatch/pull/52), [#63](https://github.com/desihub/nightwatch/pull/63))
  - Mode timeseries code from `qqa_web_app` to `webpages/timeseries.py` ([PR #56](https://github.com/desihub/nightwatch/pull/56))
  - Set up spawning of `qproc` batch jobs ([PR #45](https://github.com/desihub/nightwatch/pull/45))
  - Generate summary pages with `--summary` argument to processing ([PR #41](https://github.com/desihub/nightwatch/pull/41))
  - Setup camfiber and fibernum pages (PRs [#26](https://github.com/desihub/nightwatch/pull/26), [#27](https://github.com/desihub/nightwatch/pull/27), [#39](https://github.com/desihub/nightwatch/pull/39), [#40](https://github.com/desihub/nightwatch/pull/40))
  - Added CPU throttling on NERSC login nodes ([PR #11](https://github.com/desihub/nightwatch/pull/11))
  - Began including SNR, spectral flux, throughput from `desispec` ([PR #25](https://github.com/desihub/nightwatch/pull/25))
  - * Enabled interactive plotting through Flask web app ([PR #5](https://github.com/desihub/nightwatch/pull/5))

### Minor updates

* Bug fixes:
  - Fixed amp plotting bug ([PR #118](https://github.com/desihub/nightwatch/pull/118))
  - Fixed behavior of `monitor --catchup` for old exposure processing ([PR #107](https://github.com/desihub/nightwatch/pull/107))
  - Fixed processing and plotting bugs when running without a camera ([PR #99](https://github.com/desihub/nightwatch/pull/99))
  - Handle missing cameras ([PR #97](https://github.com/desihub/nightwatch/pull/97))
  - Fixed broken auto-refresh of exposures page in flask ap ([PR #58](https://github.com/desihub/nightwatch/pull/58))
  - Refactor camfiber pages to avoid bokeh problem with same ColumnDataSource used in two plots ([PR #53](https://github.com/desihub/nightwatch/pull/53))
* Cosmetic changes:
  - Added amp links ([PR #116](https://github.com/desihub/nightwatch/pull/116))
  - Improved readability and made plot formats consistent (PRs [#35](https://github.com/desihub/nightwatch/pull/35), [#62](https://github.com/desihub/nightwatch/pull/62), [#69](https://github.com/desihub/nightwatch/pull/69), [#89](https://github.com/desihub/nightwatch/pull/89), [#106](https://github.com/desihub/nightwatch/pull/106))
  - Have `preproc` images opened in same tab, not new pages ([PR #87](https://github.com/desihub/nightwatch/pull/87))
  - Cleaned up `preproc` and timeseries page designs (PRs [#74](https://github.com/desihub/nightwatch/pull/74), [#77](https://github.com/desihub/nightwatch/pull/77))
  - Cleaned up imports and dependencies (PRs [#55](https://github.com/desihub/nightwatch/pull/55), [#59](https://github.com/desihub/nightwatch/pull/59))
  - Optionally specify host and port for webapp ([PR #54](https://github.com/desihub/nightwatch/pull/54))
  - Adapted fibernum x-range to existing fibers ([PR #49](https://github.com/desihub/nightwatch/pull/49))
* General cleanup and documentation: PRs [#109](https://github.com/desihub/nightwatch/pull/109), [#117](https://github.com/desihub/nightwatch/pull/117), [#120](https://github.com/desihub/nightwatch/pull/120)
