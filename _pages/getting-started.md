---
layout: page
title: Getting started
seo_title: How to download CAE ML datasets safely
description: Install the Hugging Face CLI, preview large CFD repositories, select files and download AhmedML, WindsorML, DrivAerML or HiLiftAeroML safely.
permalink: /getting-started/
nav: true
nav_order: 2
eyebrow: Download guide
page_description: A storage-aware workflow for exploring and downloading multi-terabyte engineering datasets from Hugging Face.
content_class: getting-started-page
catalog_js: true
---

<aside class="guide-callout"><strong>Keep preview mode on.</strong><p>These repositories range from roughly 2 TB to 66.9 TB. Every command below includes <code>--dry-run</code> until you deliberately remove it.</p></aside>

<section class="guide-section" id="choose">
  <div class="guide-section__number">01</div>
  <div class="guide-section__content">
    <p class="section-kicker">Choose a dataset</p>
    <h2>Match complexity to the question</h2>
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
    <p class="section-kicker">Prepare the tools</p>
    <h2>Install and authenticate</h2>
    <p>Use the current <code>hf</code> command from <code>huggingface_hub</code>. <code>hf_xet</code> accelerates transfers for repositories stored with Xet.</p>
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
    <p class="section-kicker">Inspect before transfer</p>
    <h2>Preview the repository</h2>
    <p>A dry run lists the matching files and reports the planned transfer without downloading them.</p>
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
    <p class="section-kicker">Select useful files</p>
    <h2>Begin with metadata, forces and geometry</h2>
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
      <li><strong>Validate the pipeline</strong><span>Use consolidated CSV tables first.</span></li>
      <li><strong>Add geometric context</strong><span>Download STL or STEP files for shape-based models.</span></li>
      <li><strong>Train on surface physics</strong><span>Add VTP or VTU boundary files after checking storage.</span></li>
      <li><strong>Use complete flow fields</strong><span>Volume files are the final, largest tier.</span></li>
    </ol>
  </div>
</section>

<section class="guide-section" id="download">
  <div class="guide-section__number">05</div>
  <div class="guide-section__content">
    <p class="section-kicker">Download deliberately</p>
    <h2>Remove <code>--dry-run</code> only when ready</h2>
    <ul class="check-list">
      <li>Confirm the reported byte count and number of files.</li>
      <li>Allow additional working space for compressed archives and derived training data.</li>
      <li>Use a persistent filesystem; large transfers may need to resume.</li>
      <li>Record the repository revision or commit hash used by an experiment.</li>
      <li>Review dataset-specific known constraints before creating splits.</li>
    </ul>
    <a class="button button--primary" href="{{ '/datasets/' | relative_url }}">Choose a dataset and build a command</a>
  </div>
</section>

<section class="format-guide" aria-labelledby="format-guide-title">
  <p class="section-kicker">Format glossary</p><h2 id="format-guide-title">Common files in the catalog</h2>
  <dl>
    <div><dt>CSV</dt><dd>Geometry parameters, reference values and integrated force or moment coefficients.</dd></div>
    <div><dt>STL / STEP</dt><dd>Tessellated surfaces and CAD geometry suitable for geometric preprocessing.</dd></div>
    <div><dt>VTP / VTU</dt><dd>VTK polygonal or unstructured-grid data containing surface and volume fields.</dd></div>
    <div><dt>TGZ</dt><dd>Compressed archives that require extra local space when unpacked.</dd></div>
    <div><dt>NPY / JSON</dt><dd>NumPy arrays, evaluation weights, manifests and deterministic split definitions.</dd></div>
  </dl>
</section>
