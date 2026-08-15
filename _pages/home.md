---
layout: home
title: CAE ML Datasets
seo_title: High-fidelity CFD datasets for machine learning
description: Explore open, high-fidelity CFD datasets for machine-learning and physical-AI research in automotive and aerospace engineering.
permalink: /
body_class: home-body
---

<section class="home-hero" aria-labelledby="home-hero-title">
  <div class="home-hero__copy">
    <p class="eyebrow">Open data · High-fidelity simulation · Physical AI</p>
    <h1 id="home-hero-title">Engineering data for the next generation of aerodynamic models.</h1>
    <p class="home-hero__lede">Explore large-scale CFD datasets built from realistic three-dimensional geometries, validated simulation workflows and open research formats.</p>
    <div class="hero-actions">
      <a class="button button--primary" href="{{ '/datasets/' | relative_url }}">Explore the datasets</a>
      <a class="button button--ghost" href="{{ '/getting-started/' | relative_url }}">Plan a download <span aria-hidden="true">→</span></a>
    </div>
    <ul class="hero-trust" aria-label="Catalog highlights">
      <li><strong>4</strong><span>open datasets</span></li>
      <li><strong>2</strong><span>engineering domains</span></li>
      <li><strong>Up to 500M</strong><span>cells per case</span></li>
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
    <div><p class="section-kicker">Dataset catalog</p><h2 id="catalog-preview-title">From canonical bodies to complete aircraft</h2></div>
    <p>Choose a level of geometric and flow complexity that matches your model, compute budget and research question.</p>
  </div>
  <div class="dataset-grid">
    {% for item in site.data.datasets %}
      {% include dataset_card.liquid item=item %}
    {% endfor %}
  </div>
  <div class="section-cta"><a class="text-link" href="{{ '/datasets/' | relative_url }}">Compare every dataset and file format <span aria-hidden="true">→</span></a></div>
</section>

<section class="purpose-section section-block" aria-labelledby="purpose-title">
  <div class="purpose-section__intro">
    <p class="section-kicker">Why this catalog exists</p>
    <h2 id="purpose-title">Realistic data, documented well enough to use.</h2>
    <p>Open three-dimensional training data remains a bottleneck for engineering machine learning. This community-led catalog makes high-fidelity simulation data easier to discover, evaluate, download and cite.</p>
  </div>
  <div class="purpose-grid">
    <article><span aria-hidden="true">01</span><h3>Research-ready</h3><p>Geometry, integrated coefficients and rich surface or volume fields support surrogate modelling, geometric learning and reduced-order methods.</p></article>
    <article><span aria-hidden="true">02</span><h3>Traceable</h3><p>Each dataset connects simulation method, solver, publication, licence, contributors and known constraints in one place.</p></article>
    <article><span aria-hidden="true">03</span><h3>Practical at scale</h3><p>Selective download builders and dry-run commands help you inspect terabyte-scale repositories before committing storage or bandwidth.</p></article>
  </div>
</section>

<section class="workflow-section section-block" aria-labelledby="workflow-title">
  <div class="section-heading">
    <div><p class="section-kicker">A safer first download</p><h2 id="workflow-title">Go from question to usable files</h2></div>
    <p>The catalog keeps discovery separate from bulk transfer, so a quick experiment does not become a multi-terabyte surprise.</p>
  </div>
  <ol class="workflow-steps">
    <li><span>1</span><div><h3>Compare</h3><p>Match the domain, fidelity, geometry and outputs to your learning task.</p></div></li>
    <li><span>2</span><div><h3>Preview</h3><p>Generate a selective Hugging Face command with <code>--dry-run</code> enabled.</p></div></li>
    <li><span>3</span><div><h3>Download</h3><p>Start with metadata and force tables, then add geometry or fields as needed.</p></div></li>
  </ol>
  <a class="button button--secondary" href="{{ '/getting-started/' | relative_url }}">Read the getting-started guide</a>
</section>

<section class="updates-preview section-block" aria-labelledby="updates-title">
  <div class="section-heading section-heading--inline">
    <div><p class="section-kicker">Project updates</p><h2 id="updates-title">Latest from the datasets</h2></div>
    <a class="text-link" href="{{ '/news/' | relative_url }}">All updates <span aria-hidden="true">→</span></a>
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
  <div><p class="eyebrow">Community maintained</p><h2 id="contact-title">Found an issue or published with the data?</h2></div>
  <p>The datasets bring together contributors from industry and academia. Send corrections, questions or examples of downstream work to the project contact.</p>
  <a class="button button--light" href="mailto:contact@caemldatasets.org">contact@caemldatasets.org</a>
</section>
