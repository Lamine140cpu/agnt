/**
 * Rendu de gaussiennes 3D en splats, pour three.js.
 *
 * Écrit ici plutôt que vendorisé : les implémentations existantes arrivent avec
 * leur propre boucle de rendu et leur propre caméra, là où il faut une scène
 * three.js parmi d'autres, repliable dans un fichier unique.
 *
 * Le principe. Chaque gaussienne est un ellipsoïde flou. Projeté à l'écran, il
 * donne une ellipse — la covariance 3D passée par la jacobienne de la
 * projection. On dessine donc un quadrilatère par gaussienne, taillé aux axes
 * propres de cette ellipse, et le fragment y évalue la gaussienne 2D.
 *
 * Deux points de méthode :
 *
 * Les données vivent dans des textures, pas dans des attributs. Le seul
 * attribut d'instance est un indice. Trier revient alors à réécrire un tableau
 * d'entiers plutôt qu'à permuter treize flottants par gaussienne.
 *
 * Le tri est indispensable : ces surfaces sont transparentes et s'accumulent
 * de l'arrière vers l'avant. Il se fait par comptage sur seize bits, ce qui le
 * rend linéaire, et seulement quand la caméra a bougé — immobile, l'ordre
 * reste valable.
 */

const MAGIC = 0x50534d55; // « UMSP » en petit-boutiste

export async function chargerSplat(url, THREE) {
  const buf = await (await fetch(url)).arrayBuffer();
  const vue = new DataView(buf);
  if (vue.getUint32(0, true) !== MAGIC) throw new Error(`${url} : ce n'est pas un .ums`);

  const n = vue.getUint32(8, true);
  const bmin = [vue.getFloat32(12, true), vue.getFloat32(16, true), vue.getFloat32(20, true)];
  const bmax = [vue.getFloat32(24, true), vue.getFloat32(28, true), vue.getFloat32(32, true)];
  const lmin = vue.getFloat32(36, true), lmax = vue.getFloat32(40, true);
  const blocs = new Uint8Array(buf, 44, n * 17);

  const pos = new Float32Array(n * 4);
  const cov = new Float32Array(n * 8);       // deux texels : (c00,c01,c02,·) et (c11,c12,c22,·)
  const col = new Uint8Array(n * 4);

  const etendue = [bmax[0] - bmin[0], bmax[1] - bmin[1], bmax[2] - bmin[2]];
  const q = [0, 0, 0, 0], s = [0, 0, 0];

  for (let i = 0; i < n; i++) {
    const o = i * 17;
    for (let k = 0; k < 3; k++) {
      const brut = blocs[o + k * 2] | (blocs[o + k * 2 + 1] << 8);
      pos[i * 4 + k] = bmin[k] + (brut / 65535) * etendue[k];
      s[k] = Math.exp(lmin + (blocs[o + 6 + k] / 255) * (lmax - lmin));
    }
    for (let k = 0; k < 4; k++) col[i * 4 + k] = blocs[o + 9 + k];
    for (let k = 0; k < 4; k++) q[k] = (blocs[o + 13 + k] - 128) / 128;

    // covariance = R S Sᵀ Rᵀ, calculée ici une fois plutôt qu'à chaque image
    const [w, x, y, z] = q;
    const nq = Math.hypot(w, x, y, z) || 1;
    const W = w / nq, X = x / nq, Y = y / nq, Z = z / nq;
    const R = [
      1 - 2 * (Y * Y + Z * Z), 2 * (X * Y - W * Z),     2 * (X * Z + W * Y),
      2 * (X * Y + W * Z),     1 - 2 * (X * X + Z * Z), 2 * (Y * Z - W * X),
      2 * (X * Z - W * Y),     2 * (Y * Z + W * X),     1 - 2 * (X * X + Y * Y),
    ];
    // M = R · diag(s) ; Σ = M Mᵀ
    const m = [
      R[0] * s[0], R[1] * s[1], R[2] * s[2],
      R[3] * s[0], R[4] * s[1], R[5] * s[2],
      R[6] * s[0], R[7] * s[1], R[8] * s[2],
    ];
    const c = i * 8;
    cov[c + 0] = m[0] * m[0] + m[1] * m[1] + m[2] * m[2];
    cov[c + 1] = m[0] * m[3] + m[1] * m[4] + m[2] * m[5];
    cov[c + 2] = m[0] * m[6] + m[1] * m[7] + m[2] * m[8];
    cov[c + 4] = m[3] * m[3] + m[4] * m[4] + m[5] * m[5];
    cov[c + 5] = m[3] * m[6] + m[4] * m[7] + m[5] * m[8];
    cov[c + 6] = m[6] * m[6] + m[7] * m[7] + m[8] * m[8];
  }

  return { n, pos, cov, col, bmin, bmax,
           centre: bmin.map((v, k) => (v + bmax[k]) / 2) };
}

const VERT = /* glsl */`
precision highp float;
precision highp int;

/* RawShaderMaterial n'injecte aucun préambule : les matrices fournies par
   three.js doivent être déclarées à la main, contrairement à ShaderMaterial. */
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

in vec2 coin;                 // sommet du quadrilatère, dans [-2, 2]
in float indice;              // par instance

uniform highp sampler2D tPos;
uniform highp sampler2D tCov;
uniform lowp  sampler2D tCol;
/* La largeur des textures suffit à retrouver un texel, et un entier simple
   traverse three.js sans ambiguïté — un Vector2 passé pour un ivec2 arrive
   dans gl.uniform2iv, qui n'en veut pas, et l'uniforme reste à zéro. */
uniform int largeurPos, largeurCov, largeurCol;
uniform vec2 focale, fenetre;

out vec4 vCouleur;
out vec2 vQuad;

ivec2 ou(int i, int largeur){ return ivec2(i % largeur, i / largeur); }

void main(){
  int i = int(indice);
  vec3 centre = texelFetch(tPos, ou(i, largeurPos), 0).xyz;
  vec4 cam = modelViewMatrix * vec4(centre, 1.0);

  vec4 ndc = projectionMatrix * cam;
  float marge = 1.25 * ndc.w;
  if (ndc.w <= 0.0 || abs(ndc.x) > marge || abs(ndc.y) > marge) {
    gl_Position = vec4(0.0, 0.0, 2.0, 1.0); return;   // hors cadre, rejetée
  }

  vec3 a = texelFetch(tCov, ou(i * 2,     largeurCov), 0).xyz;
  vec3 b = texelFetch(tCov, ou(i * 2 + 1, largeurCov), 0).xyz;
  mat3 sigma = mat3(a.x, a.y, a.z,
                    a.y, b.x, b.y,
                    a.z, b.y, b.z);

  /* Jacobienne de la projection perspective au point visé. En colonnes, donc
     transposée par rapport à l'écriture usuelle. */
  float z = cam.z, z2 = z * z;
  mat3 J = mat3(focale.x / z, 0.0,          0.0,
                0.0,          focale.y / z, 0.0,
                -focale.x * cam.x / z2, -focale.y * cam.y / z2, 0.0);
  mat3 T = J * mat3(modelViewMatrix);
  mat3 cov = T * sigma * transpose(T);

  // dilatation d'un demi-pixel : sans elle les gaussiennes fines scintillent
  float c00 = cov[0][0] + 0.3, c01 = cov[0][1], c11 = cov[1][1] + 0.3;
  float milieu = 0.5 * (c00 + c11);
  float ecart = length(vec2(0.5 * (c00 - c11), c01));
  float l1 = milieu + ecart, l2 = milieu - ecart;
  if (l2 < 0.0) { gl_Position = vec4(0.0, 0.0, 2.0, 1.0); return; }

  /* Le grand axe de l'ellipse. Une gaussienne presque isotrope à l'écran donne
     c01 nul et l1 égal à c00 : le vecteur propre calculé est alors nul, et
     normalize en tire un NaN.

     Le garder derrière un test ne suffit pas. Un ternaire n'est pas un
     branchement : le compilateur évalue les deux membres et choisit ensuite,
     si bien que le NaN traverse la sélection et emporte le sommet — rejeté par
     la rastérisation, sans la moindre erreur, et pour la quasi-totalité des
     gaussiennes. Le cas dégénéré est donc écarté avant la normalisation, sur
     une direction toujours définie. */
  vec2 dir = abs(c01) > 1e-9 ? vec2(c01, l1 - c00)
                             : (c00 >= c11 ? vec2(1.0, 0.0) : vec2(0.0, 1.0));
  vec2 axe = dir * inversesqrt(dot(dir, dir));
  vec2 grand = min(sqrt(2.0 * l1), 1024.0) * axe;
  vec2 petit = min(sqrt(2.0 * l2), 1024.0) * vec2(axe.y, -axe.x);

  vCouleur = texelFetch(tCol, ou(i, largeurCol), 0);
  vQuad = coin;

  vec2 centreNdc = ndc.xy / ndc.w;
  gl_Position = vec4(centreNdc + (coin.x * grand + coin.y * petit) / fenetre * 2.0,
                     0.0, 1.0);
}`;

const FRAG = /* glsl */`
precision highp float;
in vec4 vCouleur;
in vec2 vQuad;
out vec4 sortie;
void main(){
  float d = -dot(vQuad, vQuad);
  if (d < -4.0) discard;                 // au-delà de deux sigmas, plus rien
  float a = exp(d) * vCouleur.a;
  sortie = vec4(vCouleur.rgb * a, a);    // alpha prémultiplié
}`;

function texture(THREE, data, texels, format, type) {
  const l = Math.min(2048, texels);
  const h = Math.ceil(texels / l);
  const canaux = format === THREE.RGBAFormat ? 4 : 4;
  const plein = type === THREE.FloatType
    ? new Float32Array(l * h * canaux) : new Uint8Array(l * h * canaux);
  plein.set(data.subarray(0, Math.min(data.length, plein.length)));
  const t = new THREE.DataTexture(plein, l, h, format, type);
  t.needsUpdate = true;
  t.minFilter = t.magFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  return t;
}

export function nuage(donnees, THREE) {
  const { n, pos, cov, col } = donnees;

  const tPos = texture(THREE, pos, n, THREE.RGBAFormat, THREE.FloatType);
  const tCov = texture(THREE, cov, n * 2, THREE.RGBAFormat, THREE.FloatType);
  const tCol = texture(THREE, col, n, THREE.RGBAFormat, THREE.UnsignedByteType);
  tCol.colorSpace = THREE.SRGBColorSpace;

  const geo = new THREE.InstancedBufferGeometry();
  geo.setAttribute('coin', new THREE.BufferAttribute(
    new Float32Array([-2, -2, 2, -2, 2, 2, -2, 2]), 2));
  geo.setIndex([0, 1, 2, 0, 2, 3]);
  const ordre = new Float32Array(n);
  for (let i = 0; i < n; i++) ordre[i] = i;
  const attrIndice = new THREE.InstancedBufferAttribute(ordre, 1);
  attrIndice.setUsage(THREE.DynamicDrawUsage);
  geo.setAttribute('indice', attrIndice);
  geo.instanceCount = n;

  const mat = new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3,
    uniforms: {
      tPos: { value: tPos }, tCov: { value: tCov }, tCol: { value: tCol },
      largeurPos: { value: tPos.image.width },
      largeurCov: { value: tCov.image.width },
      largeurCol: { value: tCol.image.width },
      focale: { value: new THREE.Vector2() },
      fenetre: { value: new THREE.Vector2() },
    },
    vertexShader: VERT, fragmentShader: FRAG,
    /* DoubleSide n'est pas un détail : (grand, petit) forme une base indirecte,
       le quadrilatère se retourne, et l'élimination des faces arrière l'efface
       en silence. C'est ce qui rendait toute la scène invisible sans qu'aucune
       erreur ne soit signalée. */
    side: THREE.DoubleSide,
    transparent: true, depthTest: false, depthWrite: false,
    blending: THREE.CustomBlending,
    blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
    blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
  });

  const maille = new THREE.Mesh(geo, mat);
  maille.frustumCulled = false;

  /* Tri par comptage sur seize bits : linéaire, sans comparaison, et sans
     allocation une fois les tampons créés. De l'arrière vers l'avant, puisque
     les gaussiennes s'accumulent par transparence. */
  const SEAUX = 65536;
  const cles = new Uint32Array(n);
  const profondeurs = new Float32Array(n);
  const comptes = new Uint32Array(SEAUX);
  const rang = new Float32Array(n);
  let dernier = null;

  function trier(camera) {
    // troisième ligne de la matrice de vue : la profondeur selon l'axe de visée
    const m = camera.matrixWorldInverse.elements;
    const d0 = -m[2], d1 = -m[6], d2 = -m[10], p = camera.position;

    // caméra immobile, ordre encore valable : le tri est le poste le plus cher
    if (dernier &&
        Math.abs(d0 - dernier[0]) + Math.abs(d1 - dernier[1]) + Math.abs(d2 - dernier[2]) < 0.0008 &&
        Math.abs(p.x - dernier[3]) + Math.abs(p.y - dernier[4]) + Math.abs(p.z - dernier[5]) < 0.02) return;
    dernier = [d0, d1, d2, p.x, p.y, p.z];

    let min = Infinity, max = -Infinity;
    for (let i = 0; i < n; i++) {
      const d = pos[i * 4] * d0 + pos[i * 4 + 1] * d1 + pos[i * 4 + 2] * d2;
      profondeurs[i] = d;
      if (d < min) min = d;
      if (d > max) max = d;
    }
    const echelle = (SEAUX - 1) / Math.max(max - min, 1e-6);
    comptes.fill(0);
    for (let i = 0; i < n; i++) {
      const k = ((profondeurs[i] - min) * echelle) | 0;
      cles[i] = k; comptes[k]++;
    }
    // cumul décroissant : le plus lointain sort en premier
    let total = 0;
    for (let k = SEAUX - 1; k >= 0; k--) { const c = comptes[k]; comptes[k] = total; total += c; }
    for (let i = 0; i < n; i++) rang[comptes[cles[i]]++] = i;

    attrIndice.array.set(rang);
    attrIndice.needsUpdate = true;
  }

  maille.onBeforeRender = (renderer, scene, camera) => {
    const taille = renderer.getDrawingBufferSize(new THREE.Vector2());
    mat.uniforms.fenetre.value.copy(taille);
    mat.uniforms.focale.value.set(
      camera.projectionMatrix.elements[0] * taille.x * 0.5,
      camera.projectionMatrix.elements[5] * taille.y * 0.5,
    );
    trier(camera);
  };

  return maille;
}
