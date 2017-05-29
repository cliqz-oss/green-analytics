# Green anaytics
As per the study Tracking the Trackers[1], ~78% of the page loads in Germany have at least one third-party tracker, almost ~42% of Page loads of Google analytics and ~22% have a Facebook tracker. Green analytics is meant to provide solutions :     A. Privacy first analytics.     B. Privacy first social sharing features. A. Privacy first analytics : The aim is to build an analytics service, which the users can use on their websites, blogs etc. The existing solutions like Google Analytics, Piwik etc all rely on server-side aggregation which means they cookies, IP or other parameters to link the message on the backend. Privacy preserving analytics service is meant to cover a wide range of use-cases: Unique visits and page loads. Returning customers. Goal conversion to track campaigns. Cross site correlations. In-site click-throughs. Visits and time in page per user (without beacons). Without having to rely on the cookies or any such thing. This approach unlike the industry de-facto standard, relies on client-side aggregation. Which means the user is the owner of the data, any only emits an aggregated event, without any identifier. Based on the implementation of Green-tracker by Josep from Cliqz[2] , Demo[3], objective at the Mozilla global sprint is to :     1. Make people aware of doing analytics in a privacy preserving manner.     2. Provide a generic script, which should be ready-to use for people who want to do analytics on their projects. Apart from just providing an analytics scripts, the task would be to provide :     1. Green analytics for websites & open-source market leading CMS like Wordpress / Drupal     2. Basic backend which collects data and generates analytics report and dashboards. If the time permits, we would also like to build a small SDK for Mobile app analytics based on the same approach. B. Privacy first social sharing features : The other very common way of tracking users across websites is adding social sharing buttons, another component of Green analytics project will be identify plugins which still allow the users to share over social media but needs explicit consent. There are already open-source solutions available for static websites / CMSes , we should not try and re-invent the wheel, instead we should create a comprehensive list of the available solutions and create a in-depth how-to guide. Footnotes: 1  Tracking the Trackers: http://www2016.net/proceedings/proceedings/p121.pdf 2. Data Collection without Privacy Side-Effects : http://josepmpujol.net/public/papers/big_green_tracker.pdf 3. Demo Green-tracker : http://site1.test.cliqz.com/


## Getting started

**TODO**

## Contributing

Thanks for your interest in contributing to *Green analytics*! There are many ways to contribute. To get started, take a look at [CONTRIBUTING.md](CONTRIBUTING.md).

## Participation Guidelines

This project adheres to a [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [michel@cliqz.com](mailto:michel@cliqz.com).

## Ideas

## MozSprint

Join us at the [Mozilla Global Sprint](http://mozilla.github.io/global-sprint/) June 1-2, 2017! We'll be gathering in-person at sites around the world and online to collaborate on this project and learn from each other. [Get your #mozsprint tickets now](http://mozilla.github.io/global-sprint/)!

![Global Sprint](https://cloud.githubusercontent.com/assets/617994/24632585/b2b07dcc-1892-11e7-91cf-f9e473187cf7.png)