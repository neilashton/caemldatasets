---
layout: page
title: Updates
seo_title: CAE ML dataset news and releases
description: Release notes, paper announcements and repository updates for AhmedML, WindsorML, DrivAerML and HiLiftAeroML.
permalink: /news/
nav: true
nav_order: 4
eyebrow: Project timeline
page_description: Dataset releases, publication milestones and catalog news from the CAE ML Datasets community.
content_class: updates-page
---

{% assign updates = site.news | sort: 'date' | reverse %}
<div class="timeline">
  {% for update in updates %}
    <article class="timeline-entry">
      <time datetime="{{ update.date | date_to_xmlschema }}"><span>{{ update.date | date: '%Y' }}</span>{{ update.date | date: '%-d %B' }}</time>
      <div class="timeline-entry__marker" aria-hidden="true"></div>
      <div class="timeline-entry__content">{{ update.content }}</div>
    </article>
  {% endfor %}
</div>

<aside class="contact-band contact-band--compact"><div><p class="eyebrow">Have an update?</p><h2>Tell us how you are using the datasets.</h2></div><p>Share corrections, derivative datasets or publications that should be linked from the catalog.</p><a class="button button--light" href="mailto:contact@caemldatasets.org">Email the project</a></aside>
