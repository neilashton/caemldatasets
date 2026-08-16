---
layout: page
title: Updates
seo_title: CAE ML dataset news and releases
description: Release notes, paper announcements and repository updates for AhmedML, WindsorML, DrivAerML and HiLiftAeroML.
permalink: /news/
nav: true
nav_order: 4
eyebrow: Project timeline
page_description: Chronological record of dataset releases, publication milestones and catalogue changes.
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

<aside class="contact-band contact-band--compact"><div><p class="eyebrow">Catalogue corrections</p><h2>Submit a correction or related publication</h2></div><p>Contact the maintainers to report repository changes, derived datasets or publications that should be included in the catalogue.</p><a class="button button--secondary" href="mailto:contact@caemldatasets.org">Contact the maintainers</a></aside>
