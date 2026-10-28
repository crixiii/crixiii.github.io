const canvas = document.getElementById("stars");
const ctx = canvas.getContext("2d");

const STAR_COUNT = 80;
let stars = [];

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function makeStars() {
  stars = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: Math.floor(Math.random() * canvas.width),
      y: Math.floor(Math.random() * canvas.height),
      size: Math.random() < 0.2 ? 4 : 2,
      speed: 0.5 + Math.random() * 1.5,
      offset: Math.random() * Math.PI * 2,
    });
  }
}

function draw(time) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const star of stars) {
    const brightness = (Math.sin(time / 1000 * star.speed + star.offset) + 1) / 2;
    ctx.fillStyle = "rgba(255, 255, 255, " + (0.2 + brightness * 0.7) + ")";
    ctx.fillRect(star.x, star.y, star.size, star.size);
  }

  requestAnimationFrame(draw);
}

window.addEventListener("resize", () => {
  resize();
  makeStars();
});

resize();
makeStars();
requestAnimationFrame(draw);
