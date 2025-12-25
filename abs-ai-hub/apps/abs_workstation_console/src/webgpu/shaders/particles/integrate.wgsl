struct Uniforms {
  timeSec: f32,
  dtSec: f32,
  gpuUtil01: f32,
  vramUtil01: f32,
  sceneId: u32,
  sceneT01: f32,
  transitionT01: f32,
  accent01: f32,
  viewport: vec2<f32>,
  center: vec2<f32>,
};

struct Particle {
  pos: vec2<f32>,
  vel: vec2<f32>,
  life: f32,
  seed: f32,
  size: f32,
  _pad: f32,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var<storage, read> PIn: array<Particle>;
@group(0) @binding(2) var<storage, read_write> POut: array<Particle>;
@group(0) @binding(3) var flowTex: texture_2d<f32>;
@group(0) @binding(4) var flowSampler: sampler;

fn hash1(x: f32) -> f32 {
  var n = fract(x * 0.1031);
  n *= n + 33.33;
  n *= n + n;
  return fract(n);
}

fn hash2(p: vec2<f32>) -> vec2<f32> {
  var h = vec3<f32>(p.xyx) * vec3<f32>(0.1031, 0.1030, 0.0973);
  h = fract(h * (h + 33.33));
  return fract((h.xx + h.yz) * h.zy);
}

fn noise2(p: vec2<f32>) -> f32 {
  let i = floor(p);
  let f = fract(p);
  var ff = f * f * (3.0 - 2.0 * f);
  
  let a = hash1(dot(i, vec2<f32>(1.0, 57.0)));
  let b = hash1(dot(i + vec2<f32>(1.0, 0.0), vec2<f32>(1.0, 57.0)));
  let c = hash1(dot(i + vec2<f32>(0.0, 1.0), vec2<f32>(1.0, 57.0)));
  let d = hash1(dot(i + vec2<f32>(1.0, 1.0), vec2<f32>(1.0, 57.0)));
  
  return mix(mix(a, b, ff.x), mix(c, d, ff.x), ff.y);
}

fn sampleFlow(pos: vec2<f32>) -> vec2<f32> {
  let uv = (pos / U.viewport);
  let flow = textureSample(flowTex, flowSampler, uv).xy;
  
  let curl = vec2<f32>(
    sin(pos.x * 0.01 + U.timeSec * 0.5) * cos(pos.y * 0.01),
    -cos(pos.x * 0.01) * sin(pos.y * 0.01 + U.timeSec * 0.5)
  ) * 0.1;
  
  return flow + curl;
}

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&PIn)) { return; }

  var p = PIn[i];
  let uv = p.pos / U.viewport;

  let flow = sampleFlow(p.pos);
  let flowStrength = mix(0.15, 1.25, U.gpuUtil01);

  var acc = flow * flowStrength;

  // Attractor for scene 3 ("spinning up")
  if (U.sceneId == 3u) {
    let d = U.center - p.pos;
    let dist = max(length(d), 1.0);
    let dir = d / dist;
    let attract = (1.0 / dist) * mix(0.0, 2.5, U.sceneT01);
    acc += dir * attract;
  }

  // Turbulence
  let t = U.timeSec * 0.35 + p.seed * 10.0;
  let n = vec2<f32>(
    noise2(p.pos * 0.01 + vec2<f32>(t, 0.0)),
    noise2(p.pos * 0.01 + vec2<f32>(0.0, t))
  ) - vec2<f32>(0.5);
  acc += n * mix(0.05, 0.45, U.gpuUtil01);

  // Integrate
  let dt = U.dtSec;
  p.vel = p.vel + acc * dt;
  p.vel *= mix(0.985, 0.94, U.gpuUtil01);
  p.pos = p.pos + p.vel * (dt * 60.0);
  p.life -= dt * 0.02;

  // Wrap / respawn
  let out = (p.pos.x < 0.0 || p.pos.y < 0.0 || p.pos.x > U.viewport.x || p.pos.y > U.viewport.y || p.life <= 0.0);
  if (out) {
    let r1 = hash1(p.seed + U.timeSec);
    let r2 = hash1(p.seed + U.timeSec * 1.7);
    p.pos = vec2<f32>(r1 * U.viewport.x, r2 * U.viewport.y);
    p.vel = vec2<f32>(0.0);
    p.life = 1.0;
    p.size = mix(1.0, 2.5, hash1(p.seed * 3.1));
  }

  POut[i] = p;
}
