---
layout: default
title: about me
permalink: /about/
---

# about me

<img class="pfp" src="{{ '/assets/images/grad.jpg' | relative_url }}" alt="me at graduation!">

I'm an research assistant at the University of Canterbury, interested in time-domain astronomy, fast transients and sky surveys. My work involves modelling fast transients, from GRBs in TESS data to FRB energetics.

- **Institution:** University of Canterbury
- **Supervisors:** Dr. Ryan Ridden-Harper, Dr. Joscha Jahns-Schindler
- **Focus:** GRBs, FRBs, time-domain astronomy, simulations

[email](mailto:montillaclarinda@gmail.com) · [github](https://github.com/crixiii) · [orcid](https://orcid.org/0009-0008-4935-069X) · [linkedin](https://www.linkedin.com/in/clarinda-m-49bb50274/)


## hobbies
{: #hobbies}

### music, arts and crafts

I play piano, guitar, and kalimba, and have played violin for 18 years. I have performed in local concert orchestras and musicals. My other creative endeavours involve knitting, crocheting, sewing, and watercolour painting. My astro-related craft projects include crocheting a JWST throw and some stars!
<div class="posters photos" data-label="hobby photos">
    <figure>
    <a href="{{ '/assets/images/Concert_Aug_2020.jpg' | relative_url }}">
      <img src="{{ '/assets/images/Concert_Aug_2020.jpg' | relative_url }}" alt="playing violin at a concert">
    </a>
    <figcaption>Performing as the concertmaster for a charity concert in 2020</figcaption>
  </figure>
    <figure>
    <a href="{{ '/assets/images/Concert_2.jpg' | relative_url }}">
      <img src="{{ '/assets/images/Concert_2.jpg' | relative_url }}" alt="playing violin at a concert">
    </a>
    </figure>
  <figure>
    <a href="{{ '/assets/images/jwst.jpg' | relative_url }}">
      <img src="{{ '/assets/images/jwst.jpg' | relative_url }}" alt="crocheted JWST mirror blanket">
    </a>
  </figure>
  <figure>
    <a href="{{ '/assets/images/star1.jpg' | relative_url }}">
      <img src="{{ '/assets/images/star1.jpg' | relative_url }}" alt="crocheted star cushion">
    </a>
  </figure>
  <figure>
    <a href="{{ '/assets/images/star2.jpg' | relative_url }}">
      <img src="{{ '/assets/images/star2.jpg' | relative_url }}" alt="crocheted star cushions">
    </a>
  </figure>
    <figure>
    <a href="{{ '/assets/images/star3.jpg' | relative_url }}">
      <img src="{{ '/assets/images/star3.jpg' | relative_url }}" alt="one crocheted star cushion">
    </a>
  </figure>
</div>

<aside class="repertoire" tabindex="0" aria-label="my music">
  <span class="repertoire-tab">♪ music</span>
  <div class="repertoire-body">
    <input type="radio" name="music" id="tab-rep" checked>
    <label for="tab-rep">selected repertoire</label>
    <input type="radio" name="music" id="tab-learn">
    <label for="tab-learn">currently learning</label>
    <div class="panel-rep">
      <h3>violin</h3>
      <ul><li>Sarasate - Introduction and Tarantelle, Op. 43</li><li>Młynarski - Mazurka, Op. 7 No. 1 </li></ul>
      <h3>piano</h3>
      <ul><li>Rachmaninoff - Prelude in C-sharp minor, Op. 3 No. 2</li><li>Sullivan - Twilight, Op. 12</li></ul>
    </div>
    <div class="panel-learn">
      <ul><li>Wieniawski - Scherzo Tarantelle, Op. 16 </li><li>Reger - Sonate, Op. 139</li></ul>
    </div>
  </div>
</aside>

<script>
(function () {
  var box = document.querySelector(".repertoire"), start = document.getElementById("hobbies");
  function update() {
    box.classList.toggle("show", start.getBoundingClientRect().top < window.innerHeight * 0.7);
  }
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  window.addEventListener("load", update);
  update();
})();
</script>
