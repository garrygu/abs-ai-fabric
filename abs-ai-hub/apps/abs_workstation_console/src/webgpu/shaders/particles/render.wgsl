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

struct VSOut {
  @builtin(position) pos: vec4<f32>,
  @location(0) localUV: vec2<f32>,
  @location(1) life: f32,
  @location(2) seed: f32,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var<storage, read> P: array<Particle>;

var<private> quad: array<vec2<f32>, 6> = array<vec2<f32>,6>(
  vec2<f32>(-1.0, -1.0),
  vec2<f32>( 1.0, -1.0),
  vec2<f32>(-1.0,  1.0),
  vec2<f32>(-1.0,  1.0),
  vec2<f32>( 1.0, -1.0),
  vec2<f32>( 1.0,  1.0)
);

@vertex
fn vsMain(
  @builtin(instance_index) iid: u32,
  @builtin(vertex_index) vid: u32
) -> VSOut {
  let p = P[iid];
  let q = quad[vid];
  let size = p.size * mix(1.0, 2.2, U.accent01);

  let ss = p.pos + q * size;
  let ndc = (ss / U.viewport) * 2.0 - vec2<f32>(1.0, 1.0);
  let clip = vec4<f32>(ndc.x, -ndc.y, 0.0, 1.0);

  var out: VSOut;
  out.pos = clip;
  out.localUV = q;
  out.life = p.life;
  out.seed = p.seed;
  return out;
}

@fragment
fn fsMain(in: VSOut) -> @location(0) vec4<f32> {
  let r = length(in.localUV);
  let soft = smoothstep(1.0, 0.0, r);
  let core = smoothstep(0.35, 0.0, r);

  let base = vec3<f32>(0.15, 0.25, 0.6);
  let accent = vec3<f32>(1.0, 0.5, 0.1);

  let c = mix(base, accent, U.accent01 * 0.6);
  let intensity = soft * 0.35 + core * mix(0.2, 1.2, U.accent01);
  let a = soft * in.life;

  return vec4<f32>(c * intensity, a);
}
