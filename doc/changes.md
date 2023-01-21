# Nightwatch change log

## 0.3.1 (unreleased)

* Updated flat standards thresholds ([PR #332](https://github.com/desihub/nightwatch/pulls/332))

## 0.3.0 (2023-01-14)

### Major Updates

* Added calibration standards for ARCS and FLATS: PRs [#326](https://github.com/desihub/nightwatch/pulls/326), [#328](https://github.com/desihub/nightwatch/pulls/328), [#329](https://github.com/desihub/nightwatch/pulls/329).
  - Stnadards defined for integrated flux (FLATS) and areas of bright lines (ARCS) in JSON format.
  - New `calibrations` module to load JSON standards for any given cal program.
  - Arc/flat cal info stored in `PER_SPECTRO` QA data structures.
  - Include plots of arc line areas and integrated fluxes to `qa-spectro*.html` pages.
  - Added of `PER_SPECTRO` exposure status to the top-level exposure table.
  - Removed disused fiber and spectro QA menu links.
  - Created static spectra QA page similar to the QA pages for amps and cameras.
* User interface improvements:
  - Classify spectra using `DESI_MASK` rather than `OBJTYPE`, useful with science targets. See PRs [#323](https://github.com/desihub/nightwatch/pulls/323), [#325](https://github.com/desihub/nightwatch/pulls/325).
  - Enable taptool to link to target images on [Legacy Survey Viewer](https://www.legacysurvey.org/viewer-desi) ([PR #309](https://github.com/desihub/nightwatch/pulls/309)).
  - Move camfiber plots into tabs for faster and easier comparisons ([PR #302](https://github.com/desihub/nightwatch/pulls/302)).
* Fixed broken assembly of fibermaps at KPNO: PRs [#313](https://github.com/desihub/nightwatch/pulls/313), [#317](https://github.com/desihub/nightwatch/pulls/317), [#318](https://github.com/desihub/nightwatch/pulls/318).

### Minor Updates

* Highlight bright unmasked pixels in DARKs ([PR #316](https://github.com/desihub/nightwatch/pulls/316)).
* Adjusted thresholds:
  - Z5 readnoise correction ([PR #305](https://github.com/desihub/nightwatch/pulls/305)).
* Cosmetic improvements to plots and tables:
  - Added spectrograph labels to CCD QA index page ([PR #312](https://github.com/desihub/nightwatch/pulls/312)).
  - Fixed broken downsampling form due to unclosed anchor tag ([PR #308](https://github.com/desihub/nightwatch/pulls/308)).
  - Fixed squashed focalplane plots in Safari ([PR #303](https://github.com/desihub/nightwatch/pulls/303)).
  - Color updates with labels for spectra ([PR #294](https://github.com/desihub/nightwatch/pulls/294)).
  - Fixed broken SurveyQA link in exposure tables ([PR #311](https://github.com/desihub/nightwatch/pulls/311)).
  - Dead SurveyQA link pointed to Survey-Ops nightqa page ([PR #293](https://github.com/desihub/nightwatch/pulls/293)).
* Documentation:
  - Fixes to help tool links on several plots: PRs [#292](https://github.com/desihub/nightwatch/pulls/292), [#295](https://github.com/desihub/nightwatch/pulls/295), [#299](https://github.com/desihub/nightwatch/pulls/299), [#300](https://github.com/desihub/nightwatch/pulls/300).
  - Modified instructions for updating Nightwatch on `cori` and `perlmutter` ([PR #306](https://github.com/desihub/nightwatch/pulls/306)).
* Fixes to enable Nightwatch processing in OS X:
  - Fix pandas "chained index" that caused mislabeling of disabled fibers ([PR #297](https://github.com/desihub/nightwatch/pulls/297)).
  - Avoid recursive subprocess creation ([PR #296](https://github.com/desihub/nightwatch/pulls/296)).

## 0.2.0 (2022-08-19)

### Major updates

* User interface improvements:
  - Redirect HelpTool links to Nightwatch wiki for most plots. (PRs [#268](https://github.com/desihub/nightwatch/pulls/268), [#269](https://github.com/desihub/nightwatch/pulls/269))
  - Fix prev/next links table and plot pages. (PRs [#227](https://github.com/desihub/nightwatch/pulls/227), [#282](https://github.com/desihub/nightwatch/pulls/282))
  - Add gridplot of CCD images for fast QA (PRs [#275](https://github.com/desihub/nightwatch/pulls/275), [#278](https://github.com/desihub/nightwatch/pulls/278))
  - Add overlay of masked pixels to CCD images. ([PR #272](https://github.com/desihub/nightwatch/pulls/272))
  - Include image masks in amplifier QA ([PR #243](https://github.com/desihub/nightwatch/pulls/243))
  - Improved camfiber and positioning plots ([PR #225](https://github.com/desihub/nightwatch/pulls/225), [#232](https://github.com/desihub/nightwatch/pulls/232))
  - Spectra plots default to calibrated versions ([PR #212](https://github.com/desihub/nightwatch/pulls/212))
  - Added more info to exposures list ([PR #205](https://github.com/desihub/nightwatch/pulls/205))
  - Added placeholder HTMLs for missing plots to avoid `ERROR not found` in links ([PR #164](https://github.com/desihub/nightwatch/pulls/164))
  - Added `surveyqa` processing and links ([PR #153](https://github.com/desihub/nightwatch/pulls/153))
  - Added guide plots page to nightwatch ([PR #151](https://github.com/desihub/nightwatch/pulls/151))
  - Added fibers-on-target and positioner accuracy plots ([PR #150](https://github.com/desihub/nightwatch/pulls/150))
* Backend processing:
  - Simplify CPU allocation at NERSC, KPNO, laptops ([PR #285](https://github.com/desihub/nightwatch/pulls/285))
  - Creation of fibermaps during exposure processing ([PR #253](https://github.com/desihub/nightwatch/pulls/253))
  - Support 2-amp readout ([PR #233](https://github.com/desihub/nightwatch/pulls/233))
  - Make calendar writing faster ([PR #184](https://github.com/desihub/nightwatch/pulls/184))
  - Updated batch processing to include plots, stop using `/tmp` ([PR #177](https://github.com/desihub/nightwatch/pulls/177))
  - Improved parallelization in preproc, amps, noise, SNR calculations (PRs [#154](https://github.com/desihub/nightwatch/pulls/154), [#159](https://github.com/desihub/nightwatch/pulls/159), [#161](https://github.com/desihub/nightwatch/pulls/161), [#167](https://github.com/desihub/nightwatch/pulls/167))
  - Addressed vulnerability on spin (PRs [#170](https://github.com/desihub/nightwatch/pulls/170), [#171](https://github.com/desihub/nightwatch/pulls/171), [#172](https://github.com/desihub/nightwatch/pulls/172))
  - Avoid NERSC I/O slowdowns by writing to temporary directory ([PR #166](https://github.com/desihub/nightwatch/pulls/166))
  - Incorporated updates to logging and `fitsio` for use at NERSC ([PR #148](https://github.com/desihub/nightwatch/pulls/148))
  - Update exposures table only for current night ([PR #130](https://github.com/desihub/nightwatch/pulls/130))

### Minor updates

* Warning and error level adjustments:
  - READNOISE thresholds (PRs [#217](https://github.com/desihub/nightwatch/pulls/217), [#229](https://github.com/desihub/nightwatch/pulls/229), [#233](https://github.com/desihub/nightwatch/pulls/233), [#245](https://github.com/desihub/nightwatch/pulls/245), [#254](https://github.com/desihub/nightwatch/pulls/254), [#274](https://github.com/desihub/nightwatch/pulls/274)).
  - COSMIC RATE thresholds (PRs [#240](https://github.com/desihub/nightwatch/pulls/240), [#254](https://github.com/desihub/nightwatch/pulls/254), [#267](https://github.com/desihub/nightwatch/pulls/267), [#290](https://github.com/desihub/nightwatch/pulls/290)).
  - ZERO + DARK thresholds (PRs [#231](https://github.com/desihub/nightwatch/pulls/231), [#236](https://github.com/desihub/nightwatch/pulls/236)).
  - TRACESHIFT thresholds (PRs [#251](https://github.com/desihub/nightwatch/pulls/251), [#256](https://github.com/desihub/nightwatch/pulls/256)).
* Documentation:
  - Added links to update instructions ([PR #266](https://github.com/desihub/nightwatch/pulls/266))
  - Added README with testing instructions at NERSC (PRs [#246](https://github.com/desihub/nightwatch/pulls/246), [#247](https://github.com/desihub/nightwatch/pulls/247), [#248](https://github.com/desihub/nightwatch/pulls/248))
  - Added docs for updating docker on rancher 2 ([PR #174](https://github.com/desihub/nightwatch/pulls/174))
* Bug fixes:
  - Fixed a bug in reporting qproc fails for the summary tables ([PR #262](https://github.com/desihub/nightwatch/pulls/262))
  - Fixed fibers-on-target scale problems ([PR #250](https://github.com/desihub/nightwatch/pulls/250))
  - Environment variable guard check to avoid crashes at KPNO ([PR #244](https://github.com/desihub/nightwatch/pulls/244))
  - Handle `NIGHT=None` cases in exposure header ([PR #215](https://github.com/desihub/nightwatch/pulls/215))
  - Plot robustness ([PR #187](https://github.com/desihub/nightwatch/pulls/187)); handle coordinates files with and without FIBER column ([PR #189](https://github.com/desihub/nightwatch/pulls/189))
  - Corrected random spectra selection and plotting ([PR #181](https://github.com/desihub/nightwatch/pulls/181))
  - Bytestr/str fixes for pandas and bokeh 2.2 ([PR #178](https://github.com/desihub/nightwatch/pulls/178))
  - Improved focal plane plot color scaling ([PR #176](https://github.com/desihub/nightwatch/pulls/176))
  - Fixed compatibility issues with `fitsio` ([PR #168](https://github.com/desihub/nightwatch/pulls/168))
  - Fixed incorrect handling of `qproc` errors ([PR #165](https://github.com/desihub/nightwatch/pulls/165))
  - Fixed amp axis labels ([PR #158](https://github.com/desihub/nightwatch/pulls/158))
  - Handle errors due to missing guide-rois (PRs [#155](https://github.com/desihub/nightwatch/pulls/155), [#157](https://github.com/desihub/nightwatch/pulls/157))
  - Fixed spectra plotting with mismatched fibermaps ([PR #129](https://github.com/desihub/nightwatch/pulls/129))
  - Updated to new `OBSTYPE` keyword instead of `FLAVOR` ([PR #126](https://github.com/desihub/nightwatch/pulls/126))
* Cosmetic updates:
  - Made docker directory neater/easier to pull and use without much modification ([PR #173](https://github.com/desihub/nightwatch/pulls/173))
  - Blank pixels filled in rotated guide images ([PR #163](https://github.com/desihub/nightwatch/pulls/163))

## 0.1.0 (2019-10-02)

Release for DESI Commissioning

* Cleanup ([PR #120](https://github.com/desihub/nightwatch/pulls/120))
* rename qqa -> nightwatch ([PR #119](https://github.com/desihub/nightwatch/pulls/119))
* fixed amp plotting bug ([PR #118](https://github.com/desihub/nightwatch/pulls/118))
* Cleaning up/adding documentation ([PR #117](https://github.com/desihub/nightwatch/pulls/117))
* Amp links ([PR #116](https://github.com/desihub/nightwatch/pulls/116))
* added log axis to camfiber plots ([PR #114](https://github.com/desihub/nightwatch/pulls/114))
* Added docker configuration files ([PR #112](https://github.com/desihub/nightwatch/pulls/112))
* switched over from fitsio to astropy ([PR #111](https://github.com/desihub/nightwatch/pulls/111))
* Fix downsampling error ([PR #110](https://github.com/desihub/nightwatch/pulls/110))
* Cleanup branch ([PR #109](https://github.com/desihub/nightwatch/pulls/109))
* Track failed exps ([PR #108](https://github.com/desihub/nightwatch/pulls/108))
* fixed qqa monitor --catchup ([PR #107](https://github.com/desihub/nightwatch/pulls/107))
* Improving readability and making plot formats consistent ([PR #106](https://github.com/desihub/nightwatch/pulls/106))
* Qproc fail tracking ([PR #101](https://github.com/desihub/nightwatch/pulls/101))
* Log flagging ([PR #100](https://github.com/desihub/nightwatch/pulls/100))
* fix bug when running with single camera ([PR #99](https://github.com/desihub/nightwatch/pulls/99))
* Generating summary fits file and using it in timeseries ([PR #98](https://github.com/desihub/nightwatch/pulls/98))
* no np.min() np.max() for empty array ([PR #97](https://github.com/desihub/nightwatch/pulls/97))
* added processed as argument to find_unprocessed_expdir ([PR #96](https://github.com/desihub/nightwatch/pulls/96))
* Robustness ([PR #92](https://github.com/desihub/nightwatch/pulls/92))
* added logfile viewing capabilities ([PR #91](https://github.com/desihub/nightwatch/pulls/91))
* spectro metadata col in exposures table ([PR #90](https://github.com/desihub/nightwatch/pulls/90))
* Aesthetics ([PR #89](https://github.com/desihub/nightwatch/pulls/89))
* Add startdate ([PR #88](https://github.com/desihub/nightwatch/pulls/88))
* Same tab preproc ([PR #87](https://github.com/desihub/nightwatch/pulls/87))
* Spectra nav ([PR #79](https://github.com/desihub/nightwatch/pulls/79))
* Skipping empty directories in qqa-monitor ([PR #78](https://github.com/desihub/nightwatch/pulls/78))
* Timeseries redesign ([PR #77](https://github.com/desihub/nightwatch/pulls/77))
* Preproc redesign ([PR #74](https://github.com/desihub/nightwatch/pulls/74))
* Camfiber to spectra ([PR #73](https://github.com/desihub/nightwatch/pulls/73))
* closed/joined pools in run.py ([PR #72](https://github.com/desihub/nightwatch/pulls/72))
* Adding thresholds branch ([PR #70](https://github.com/desihub/nightwatch/pulls/70))
* fixed camfib-axes for summary page, to match amp plots aesthetic ([PR #69](https://github.com/desihub/nightwatch/pulls/69))
* added frame option to spectra plots ([PR #68](https://github.com/desihub/nightwatch/pulls/68))
* Auto-updating latest exposure summary ([PR #63](https://github.com/desihub/nightwatch/pulls/63))
* resized plot heights ([PR #62](https://github.com/desihub/nightwatch/pulls/62))
* Squished plot fix ([PR #61](https://github.com/desihub/nightwatch/pulls/61))
* Amp line plot ([PR #60](https://github.com/desihub/nightwatch/pulls/60))
* changed QARunner imports and qa __init__ file ([PR #59](https://github.com/desihub/nightwatch/pulls/59))
* changed cached max age ([PR #58](https://github.com/desihub/nightwatch/pulls/58))
* moved code from qqa_web_app to webpages/timeseries.py ([PR #56](https://github.com/desihub/nightwatch/pulls/56))
* Remove webpage module dep ([PR #55](https://github.com/desihub/nightwatch/pulls/55))
* optionally specify host and port for webapp ([PR #54](https://github.com/desihub/nightwatch/pulls/54))
* Camfib webpage generation ([PR #53](https://github.com/desihub/nightwatch/pulls/53))
* Auto-reload exposures table when changed ([PR #52](https://github.com/desihub/nightwatch/pulls/52))
* exptime to exposures table ([PR #51](https://github.com/desihub/nightwatch/pulls/51))
* fibernum x-range plots ([PR #49](https://github.com/desihub/nightwatch/pulls/49))
* added spectra plots to flask app ([PR #48](https://github.com/desihub/nightwatch/pulls/48))
* Qproc batch job ([PR #45](https://github.com/desihub/nightwatch/pulls/45))
* Cleanup ([PR #43](https://github.com/desihub/nightwatch/pulls/43))
* Summary json branch ([PR #41](https://github.com/desihub/nightwatch/pulls/41))
* Fibernum default webpage ([PR #40](https://github.com/desihub/nightwatch/pulls/40))
* Per fibernum ([PR #39](https://github.com/desihub/nightwatch/pulls/39))
* replaced amp graph with line graph ([PR #35](https://github.com/desihub/nightwatch/pulls/35))
* removed PER_CAMFIBER item from json dictionary when autogenerating ([PR #27](https://github.com/desihub/nightwatch/pulls/27))
* Camfiber features ([PR #26](https://github.com/desihub/nightwatch/pulls/26))
* SNR - spectral flux - Throughput  ([PR #25](https://github.com/desihub/nightwatch/pulls/25))
* Camera qa branch ([PR #24](https://github.com/desihub/nightwatch/pulls/24))
* New pregenerate image branch ([PR #23](https://github.com/desihub/nightwatch/pulls/23))
* Fiber flat QA ([PR #22](https://github.com/desihub/nightwatch/pulls/22))
* added pregenerating downsampled x4 images when running run.py ([PR #21](https://github.com/desihub/nightwatch/pulls/21))
* refactored all camfiber code to support columndatasource ([PR #20](https://github.com/desihub/nightwatch/pulls/20))
* Hdu name timeseries branch ([PR #17](https://github.com/desihub/nightwatch/pulls/17))
* Input calendar timeseries branch ([PR #16](https://github.com/desihub/nightwatch/pulls/16))
* added following line to timeseries ([PR #15](https://github.com/desihub/nightwatch/pulls/15))
* Basic timeseries ([PR #13](https://github.com/desihub/nightwatch/pulls/13))
* More camfib plots ([PR #12](https://github.com/desihub/nightwatch/pulls/12))
* add CPU throttling on NERSC login nodes ([PR #11](https://github.com/desihub/nightwatch/pulls/11))
* changed camfiber plots to percentile for dynamic ranges ([PR #10](https://github.com/desihub/nightwatch/pulls/10))
* Trace shift ([PR #9](https://github.com/desihub/nightwatch/pulls/9))
* Noise correlation ([PR #8](https://github.com/desihub/nightwatch/pulls/8))
* Auto ([PR #6](https://github.com/desihub/nightwatch/pulls/6))
* Flask web app branch ([PR #5](https://github.com/desihub/nightwatch/pulls/5))
* added ability to click on an amp tile ([PR #4](https://github.com/desihub/nightwatch/pulls/4))
* Qol expo changes branch ([PR #3](https://github.com/desihub/nightwatch/pulls/3))
* Qol cal changes branch ([PR #2](https://github.com/desihub/nightwatch/pulls/2))
* Calendar nights branch ([PR #1](https://github.com/desihub/nightwatch/pulls/1))
