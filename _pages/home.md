---
layout: home
title: CAE ML Datasets
seo_title: Computational fluid dynamics datasets for machine learning
description: Catalogue of open CFD datasets for machine-learning research in automotive and aerospace engineering, with methods, publications and data-access guidance.
permalink: /
body_class: home-body
---

<section class="home-hero" aria-labelledby="home-hero-title">
  <div class="home-hero__copy">
    <p class="eyebrow">Computational fluid dynamics data catalogue</p>
    <h1 id="home-hero-title">Open CFD datasets for engineering machine-learning research</h1>
    <p class="home-hero__lede">The catalogue documents four simulation datasets covering automotive external aerodynamics and high-lift aircraft flows. Each record summarises the geometry, numerical method, available data products, licence and associated publication.</p>
    <div class="hero-actions">
      <a class="button button--primary" href="{{ '/datasets/' | relative_url }}">View dataset catalogue</a>
      <a class="button button--ghost" href="{{ '/getting-started/' | relative_url }}">Data access guide <span aria-hidden="true">→</span></a>
    </div>
    <ul class="hero-trust" aria-label="Catalogue summary">
      <li><strong>4</strong><span>datasets in the catalogue</span></li>
      <li><strong>2</strong><span>application domains</span></li>
      <li><strong>Up to 500M</strong><span>cells in an individual case</span></li>
    </ul>
  </div>
  <div class="home-hero__visual" aria-label="Computational fluid dynamics flow-field visualization">
    <img src="{{ '/assets/img/autocfd2.png' | relative_url }}" alt="Abstract computational fluid dynamics streamlines in blue, teal and amber" loading="eager" decoding="async">
    <div class="hero-data-card hero-data-card--top"><span>Automotive</span><strong>Ahmed · Windsor · DrivAer</strong></div>
    <div class="hero-data-card hero-data-card--bottom"><span>Aerospace</span><strong>HiLiftAeroML · 1,800 cases</strong></div>
  </div>
</section>

<section class="catalog-preview section-block" aria-labelledby="catalog-preview-title">
  <div class="section-heading">
    <div><p class="section-kicker">Catalogue</p><h2 id="catalog-preview-title">Datasets and simulation scope</h2></div>
    <p>The collection ranges from parameterised bluff bodies to a complete high-lift aircraft configuration, with different numerical methods and data volumes.</p>
  </div>
  <div class="dataset-grid">
    {% for item in site.data.datasets %}
      {% include dataset_card.liquid item=item %}
    {% endfor %}
  </div>
  <div class="section-cta"><a class="text-link" href="{{ '/datasets/' | relative_url }}">View the technical comparison <span aria-hidden="true">→</span></a></div>
</section>

<section class="purpose-section section-block" aria-labelledby="purpose-title">
  <div class="purpose-section__intro">
    <p class="section-kicker">About the catalogue</p>
    <h2 id="purpose-title">Scope and documentation</h2>
    <p>This site collates dataset-level information needed to assess suitability for a research task. It complements, rather than replaces, the repository documentation and source publications linked from each record.</p>
  </div>
  <div class="purpose-grid">
    <article><span aria-hidden="true">01</span><h3>Data products</h3><p>Records distinguish geometry, integrated coefficients, surface fields, volume fields and derived data products.</p></article>
    <article><span aria-hidden="true">02</span><h3>Methods and provenance</h3><p>Simulation method, solver, publication, licence, contributors and documented limitations are reported together.</p></article>
    <article><span aria-hidden="true">03</span><h3>Access considerations</h3><p>File-selection examples and dry-run commands are provided because the complete repositories range from approximately 2 TB to 66.9 TB.</p></article>
  </div>
</section>

<section class="workflow-section section-block" aria-labelledby="workflow-title">
  <div class="section-heading">
    <div><p class="section-kicker">Data access</p><h2 id="workflow-title">Recommended sequence for initial access</h2></div>
    <p>Because the repositories are multi-terabyte, file lists and transfer sizes should normally be inspected before data are downloaded.</p>
  </div>
  <ol class="workflow-steps">
    <li><span>1</span><div><h3>Select</h3><p>Compare domain, geometry, numerical method and available data products.</p></div></li>
    <li><span>2</span><div><h3>Estimate</h3><p>Use a selective Hugging Face command with <code>--dry-run</code> enabled.</p></div></li>
    <li><span>3</span><div><h3>Transfer</h3><p>Retrieve the required tables, geometry or field data after reviewing the estimate.</p></div></li>
  </ol>
  <a class="button button--secondary" href="{{ '/getting-started/' | relative_url }}">Read the data access guide</a>
</section>

<section class="updates-preview section-block" aria-labelledby="updates-title">
  <div class="section-heading section-heading--inline">
    <div><p class="section-kicker">Release record</p><h2 id="updates-title">Dataset releases and publications</h2></div>
    <a class="text-link" href="{{ '/news/' | relative_url }}">View all updates <span aria-hidden="true">→</span></a>
  </div>
  {% assign recent_updates = site.news | sort: 'date' | reverse %}
  <div class="updates-list">
    {% for update in recent_updates limit: 3 %}
      <article class="update-row">
        <time datetime="{{ update.date | date_to_xmlschema }}">{{ update.date | date: '%-d %b %Y' }}</time>
        <div>{{ update.content }}</div>
      </article>
    {% endfor %}
  </div>
</section>

<section class="contact-band" aria-labelledby="contact-title">
  <div><p class="eyebrow">Catalogue maintenance</p><h2 id="contact-title">Corrections and related publications</h2></div>
  <p>Contact the maintainers to report a catalogue error, repository change, derived dataset or publication that uses these data.</p>
  <a class="button button--secondary" href="mailto:contact@caemldatasets.org">Contact the maintainers</a>
</section>
