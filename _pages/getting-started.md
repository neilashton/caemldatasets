---
layout: page
title: Data access
seo_title: Accessing the CAE ML datasets
description: Instructions for using the Hugging Face command-line client to inspect and retrieve selected files from AhmedML, WindsorML, DrivAerML and HiLiftAeroML.
permalink: /getting-started/
nav: true
nav_order: 2
eyebrow: Data access
page_description: Hugging Face client commands, file-selection examples and storage considerations for the datasets in this catalogue.
content_class: getting-started-page
catalog_js: true
---

<aside class="guide-callout"><strong>Repository sizes</strong><p>The complete repositories range from approximately 2 TB to 66.9 TB. The examples use <code>--dry-run</code> so that file lists and transfer sizes can be inspected before retrieval.</p></aside>

<section class="guide-section" id="choose">
  <div class="guide-section__number">01</div>
  <div class="guide-section__content">
    <p class="section-kicker">Dataset selection</p>
    <h2>Select by domain, geometry and numerical method</h2>
    <div class="choice-grid">
      {% for item in site.data.datasets %}
        <a href="{{ item.permalink | relative_url }}"><span>{{ item.domain }} · {{ item.geometry }}</span><strong>{{ item.name }}</strong><small>{{ item.cases }} · {{ item.method }} · {{ item.size }}</small></a>
      {% endfor %}
    </div>
  </div>
</section>

<section class="guide-section" id="install">
  <div class="guide-section__number">02</div>
  <div class="guide-section__content">
    <p class="section-kicker">Client setup</p>
    <h2>Install the Hugging Face command-line client</h2>
    <p>The <code>hf</code> command is provided by <code>huggingface_hub</code>. The optional <code>hf_xet</code> package supports repositories stored with Xet.</p>
    <div class="command-card">
      <div class="command-card__header"><strong>Terminal</strong><button type="button" data-copy="#guide-install-command">Copy</button></div>
      <pre id="guide-install-command"><code>python -m pip install -U huggingface_hub hf_xet
hf auth login</code></pre>
    </div>
    <p class="fine-print">The datasets are public. Authentication is still useful for reliable Hub access and higher rate limits; keep tokens out of scripts and repositories.</p>
  </div>
</section>

<section class="guide-section" id="preview">
  <div class="guide-section__number">03</div>
  <div class="guide-section__content">
    <p class="section-kicker">Repository inspection</p>
    <h2>Estimate a transfer with <code>--dry-run</code></h2>
    <p>A dry run lists matching files and reports the estimated transfer without downloading them.</p>
    <div class="command-card">
      <div class="command-card__header"><strong>AhmedML full-repository preview</strong><button type="button" data-copy="#guide-preview-command">Copy</button></div>
      <pre id="guide-preview-command"><code>hf download neashton/ahmedml \
  --type dataset \
  --local-dir ./ahmedml_data \
  --dry-run</code></pre>
    </div>
    <p>Replace the repository ID with <code>neashton/windsorml</code>, <code>neashton/drivaerml</code> or <code>nvidia/HiLiftAeroML</code>. Each dataset page provides a builder for its actual file patterns.</p>
  </div>
</section>

<section class="guide-section" id="select">
  <div class="guide-section__number">04</div>
  <div class="guide-section__content">
    <p class="section-kicker">File selection</p>
    <h2>Select data products explicitly</h2>
    <div class="command-card">
      <div class="command-card__header"><strong>Selective AhmedML preview</strong><button type="button" data-copy="#guide-select-command">Copy</button></div>
      <pre id="guide-select-command"><code>hf download neashton/ahmedml \
  --type dataset \
  --local-dir ./ahmedml_data \
  --include "force_mom_all.csv" \
  --include "geo_parameters_all.csv" \
  --include "run_*/ahmed_*.stl" \
  --dry-run</code></pre>
    </div>
    <ol class="decision-list">
      <li><strong>Tabular data</strong><span>Consolidated CSV files contain geometry parameters and integrated coefficients.</span></li>
      <li><strong>Geometry</strong><span>STL or STEP files provide geometric input for shape-based models.</span></li>
      <li><strong>Surface fields</strong><span>VTP or VTU boundary files contain spatially resolved surface quantities.</span></li>
      <li><strong>Volume fields</strong><span>Three-dimensional field files have the largest storage and processing requirements.</span></li>
    </ol>
  </div>
</section>

<section class="guide-section" id="download">
  <div class="guide-section__number">05</div>
  <div class="guide-section__content">
    <p class="section-kicker">Transfer</p>
    <h2>Review the estimate before removing <code>--dry-run</code></h2>
    <ul class="check-list">
      <li>Confirm the reported byte count and number of files.</li>
      <li>Allow additional working space for compressed archives and derived training data.</li>
      <li>Use a persistent filesystem; large transfers may need to resume.</li>
      <li>Record the repository revision or commit hash used by an experiment.</li>
      <li>Review dataset-specific known constraints before creating splits.</li>
    </ul>
    <a class="button button--primary" href="{{ '/datasets/' | relative_url }}">Open the dataset catalogue</a>
  </div>
</section>

<section class="format-guide" aria-labelledby="format-guide-title">
  <p class="section-kicker">File formats</p><h2 id="format-guide-title">Formats used in the catalogue</h2>
  <dl>
    <div><dt>CSV</dt><dd>Geometry parameters, reference values and integrated force or moment coefficients.</dd></div>
    <div><dt>STL / STEP</dt><dd>Tessellated surfaces and CAD geometry suitable for geometric preprocessing.</dd></div>
    <div><dt>VTP / VTU</dt><dd>VTK polygonal or unstructured-grid data containing surface and volume fields.</dd></div>
    <div><dt>TGZ</dt><dd>Compressed archives that require extra local space when unpacked.</dd></div>
    <div><dt>NPY / JSON</dt><dd>NumPy arrays, evaluation weights, manifests and deterministic split definitions.</dd></div>
  </dl>
</section>
