# 0x0128: marca

## Logo

Un búho que también es un escudo, hecho con nueve barras verticales. Los dos ojos son los dos ceros de `0x0128`.

| Archivo | Uso |
|---|---|
| `assets/logo/0x0128-logo-negro.svg` | Sobre fondos claros |
| `assets/logo/0x0128-logo-blanco.svg` | Sobre fondos oscuros |
| `assets/logo/0x0128-avatar-fondo-negro-1024px.png` | Foto de perfil (GitHub, LinkedIn, Medium) |

No se recolorea, no se estira y no se le añaden sombras ni contornos.

## Color

Solo blanco y negro, con grises para el texto secundario.

| Tema oscuro | Tema claro | Para qué |
|---|---|---|
| `#000000` / `#0A0A0A` | `#FFFFFF` | Fondo |
| `#F5F5F5` | `#0A0A0A` | Texto principal y logo |
| `#8C8C8C` | `#6B6B6B` | Texto secundario |
| `#2A2A2A` | `#E0E0E0` | Bordes y líneas |

## Cómo cambiar algo

Los textos del banner, la tarjeta `whoami`, el radar de skills, las cabeceras de proyecto y las etiquetas están en `brand.json`. Después de editarlo:

```
python3 scripts/build.py
```

Genera cada imagen dos veces, para el tema oscuro y el claro de GitHub. No necesita instalar nada, solo Python 3.

El radar (`radar.axes`) no muestra notas fijas: cada eje se mueve entre un mínimo y un máximo (de 0 a 100). Ajusta esos rangos a tu gusto.
