---
layout: page
title: Datasets
seo_title: CFD dataset catalogue for engineering machine learning
description: Technical comparison of AhmedML, WindsorML, DrivAerML and HiLiftAeroML by domain, case count, numerical method, file format, licence and repository size.
permalink: /datasets/
nav: true
nav_order: 1
eyebrow: Dataset catalogue
page_description: Technical summary of four CFD datasets spanning simplified automotive bodies, realistic road vehicles and a complete high-lift aircraft configuration.
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
    <div><p class="section-kicker">Technical comparison</p><h2 id="comparison-title">Dataset scope and data volume</h2></div>
    <p>Stored sizes are approximate and may change with repository revisions. Transfer estimates should be checked before field data are retrieved.</p>
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
  <div><p class="eyebrow">Data selection</p><h2>Select data products according to the analysis requirements.</h2></div>
  <p>Tabular coefficients and geometry can be used to validate an initial pipeline. Surface and three-dimensional volume fields require progressively greater storage and processing capacity.</p>
  <a class="button button--secondary" href="{{ '/getting-started/' | relative_url }}">Data access guidance</a>
</aside>
