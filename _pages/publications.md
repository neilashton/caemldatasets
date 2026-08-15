---
layout: page
title: Publications
seo_title: Publications for the CAE ML datasets
description: Read and cite the source publications for AhmedML, WindsorML, DrivAerML and HiLiftAeroML.
permalink: /publications/
nav: true
nav_order: 3
eyebrow: Research record
page_description: Source papers, dataset repositories and persistent identifiers for the datasets in this catalog.
content_class: publications-page
---

<div class="publication-list">
  {% assign papers = site.data.datasets | reverse %}
  {% for item in papers %}
    <article class="publication-card">
      <div class="publication-card__year"><span>{{ item.published | date: '%Y' }}</span></div>
      <div class="publication-card__content">
        <p class="eyebrow"><a href="{{ item.permalink | relative_url }}">{{ item.name }}</a> · {{ item.domain }}</p>
        <h2><a href="{{ item.paper_url }}">{{ item.paper_title }}</a></h2>
        <p>{{ item.description }}</p>
        <div class="publication-card__meta">
          {% if item.name == 'WindsorML' %}<span>NeurIPS 2024 · Datasets and Benchmarks Track</span>{% else %}<span>arXiv:{{ item.arxiv_id }}</span>{% endif %}
          <span>{{ item.license }}</span>
        </div>
        <div class="publication-card__links">
          <a class="button button--secondary" href="{{ item.paper_url }}">Read paper <span aria-hidden="true">↗</span></a>
          <a class="text-link" href="{{ item.huggingface_url }}">Dataset repository <span aria-hidden="true">↗</span></a>
          {% if item.doi %}<a class="text-link" href="https://doi.org/{{ item.doi }}">DOI {{ item.doi }} <span aria-hidden="true">↗</span></a>{% endif %}
        </div>
      </div>
    </article>
  {% endfor %}
</div>

<aside class="citation-guidance"><div><p class="eyebrow">Citing the data</p><h2>Use the paper and the dataset identifier.</h2></div><p>Every dataset page provides copy-ready BibTeX. Where a Hugging Face DOI is available, include it alongside the source paper and record the repository revision used by your experiment.</p></aside>
