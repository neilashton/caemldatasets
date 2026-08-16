---
layout: page
title: Datasets
seo_title: Open CFD datasets for engineering machine learning
description: Compare AhmedML, WindsorML, DrivAerML and HiLiftAeroML by domain, scale, simulation method, file format, licence and repository size.
permalink: /datasets/
nav: true
nav_order: 1
eyebrow: Dataset catalog
page_description: Four open, high-fidelity CFD datasets spanning simplified automotive bodies, realistic road vehicles and complete high-lift aircraft.
content_class: catalog-page
catalog_js: true
---

<div class="catalog-toolbar" data-catalog-filter>
  <div class="filter-group" role="group" aria-label="Filter datasets by engineering domain">
    <button type="button" class="filter-button is-active" data-filter="all" aria-pressed="true">All datasets <span>4</span></button>
    <button type="button" class="filter-button" data-filter="automotive" aria-pressed="false">Automotive <span>3</span></button>
    <button type="button" class="filter-button" data-filter="aerospace" aria-pressed="false">Aerospace <span>1</span></button>
  </div>
  <p class="catalog-count" aria-live="polite"><span data-catalog-count>4</span> datasets shown</p>
</div>

<div class="dataset-grid dataset-grid--catalog">
  {% for item in site.data.datasets %}
    {% include dataset_card.liquid item=item %}
  {% endfor %}
</div>

<section class="comparison-section" aria-labelledby="comparison-title">
  <div class="section-heading">
    <div><p class="section-kicker">Side-by-side</p><h2 id="comparison-title">Compare technical scope</h2></div>
    <p>Repository sizes are approximate. Always run a selective preview before transferring field data.</p>
  </div>
  <div class="data-table-wrap" role="region" aria-label="Dataset comparison" tabindex="0">
    <table class="data-table comparison-table">
      <thead><tr><th>Dataset</th><th>Domain</th><th>Scale</th><th>Method</th><th>Resolution</th><th>Stored size</th><th>Licence</th></tr></thead>
      <tbody>
        {% for item in site.data.datasets %}
          <tr data-catalog-row data-domain="{{ item.domain | downcase }}">
            <th scope="row"><a href="{{ item.permalink | relative_url }}">{{ item.name }}</a><small>{{ item.geometry }}</small></th>
            <td>{{ item.domain }}</td><td>{{ item.cases }}</td><td>{{ item.method }}</td><td>{{ item.resolution }}</td><td>{{ item.size }}</td><td><a href="{{ item.license_url }}">{{ item.license }}</a></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<aside class="catalog-guidance">
  <div><p class="eyebrow">Unsure where to begin?</p><h2>Start with the smallest useful representation.</h2></div>
  <p>Force tables and geometry are usually enough to validate a pipeline. Add surface fields next; full three-dimensional volume data has the highest storage and processing cost.</p>
  <a class="button button--secondary" href="{{ '/getting-started/' | relative_url }}">Plan your first download</a>
</aside>
