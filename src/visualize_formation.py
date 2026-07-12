# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import math
import zipfile
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle, Circle, Arc
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageOps, ImageDraw


# ============================================================
# FORMASYONLAR VE STİLLER
# ============================================================

FORMATIONS = {
    "4-3-3": {"G": 1, "D": 4, "M": 3, "F": 3},
    "4-4-2": {"G": 1, "D": 4, "M": 4, "F": 2},
    "4-2-3-1": {"G": 1, "D": 4, "M": 3, "F": 4},
    "3-4-3": {"G": 1, "D": 3, "M": 4, "F": 3},
    "3-5-2": {"G": 1, "D": 3, "M": 5, "F": 2},
    "5-3-2": {"G": 1, "D": 5, "M": 3, "F": 2},
    "4-5-1": {"G": 1, "D": 4, "M": 5, "F": 1},
}

TEAM_META = {
    "Algeria": "ALG",
    "Argentina": "ARG",
    "Belgium": "BEL",
    "Bosnia & Herzegovina": "BIH",
    "Brazil": "BRA",
    "Cabo Verde": "CPV",
    "Canada": "CAN",
    "Colombia": "COL",
    "Curaçao": "CUW",
    "Côte d'Ivoire": "CIV",
    "Egypt": "EGY",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Iran": "IRN",
    "Japan": "JPN",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Norway": "NOR",
    "Paraguay": "PAR",
    "Portugal": "POR",
    "Senegal": "SEN",
    "South Korea": "KOR",
    "Spain": "ESP",
    "Sweden": "SWE",
    "Switzerland": "SUI",
    "Türkiye": "TUR",
    "USA": "USA",
}

POSITION_STYLE = {
    "G": {"face": "#21c7f6", "label": "GK"},
    "D": {"face": "#ff9f1c", "label": "DEF"},
    "M": {"face": "#a66cff", "label": "MID"},
    "F": {"face": "#ff4f7b", "label": "FWD"},
}

# Dikey saha yerleşimi
ROW_Y = {
    "G": 10,
    "D": 34,
    "M": 62,
    "F": 89,
}

FIGSIZE = (18, 11)
DPI = 300

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def safe_filename(text: str) -> str:
    return (
        str(text)
        .replace(" ", "_")
        .replace(".", "")
        .replace("/", "-")
        .replace(":", "-")
    )


def team_code(team_name: str) -> str:
    return TEAM_META.get(team_name, str(team_name)[:3].upper())


def shorten_name(name: str, max_len: int = 17) -> str:
    name = str(name)

    if len(name) <= max_len:
        return name

    parts = name.split()

    if len(parts) == 1:
        return name[: max_len - 1] + "…"

    candidate = f"{parts[0][0]}. {parts[-1]}"

    if len(candidate) <= max_len:
        return candidate

    return candidate[: max_len - 1] + "…"


def row_x_positions(count: int) -> list[float]:
    """
    Oyuncuları 68 metre genişliğindeki saha boyunca eşit aralıkla dağıtır.
    """
    if count <= 1:
        return [34]

    left = 7
    right = 61
    step = (right - left) / (count - 1)

    return [left + i * step for i in range(count)]


def get_player_coordinates(
    formation_name: str,
    formation_slot: str,
) -> tuple[float, float]:

    position = str(formation_slot)[0]
    slot_number = int(str(formation_slot)[1:])

    count = FORMATIONS[formation_name][position]
    x_positions = row_x_positions(count)

    return x_positions[slot_number - 1], ROW_Y[position]


# ============================================================
# BAYRAK ÇİZİMLERİ
# ============================================================

def make_flag_image(
    team_name: str,
    width: int = 72,
    height: int = 48,
) -> Image.Image:

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    def horizontal(colors, ratios=None):
        ratios = ratios or [1] * len(colors)
        total = sum(ratios)
        y = 0

        for color, ratio in zip(colors, ratios):
            next_y = round(y + height * ratio / total)
            draw.rectangle((0, y, width, next_y), fill=color)
            y = next_y

    def vertical(colors, ratios=None):
        ratios = ratios or [1] * len(colors)
        total = sum(ratios)
        x = 0

        for color, ratio in zip(colors, ratios):
            next_x = round(x + width * ratio / total)
            draw.rectangle((x, 0, next_x, height), fill=color)
            x = next_x

    def cross(background, outer, inner=None):
        draw.rectangle((0, 0, width, height), fill=background)

        outer_w = max(5, width // 7)
        outer_h = max(5, height // 6)
        cx = width * 0.42
        cy = height / 2

        draw.rectangle(
            (cx - outer_w / 2, 0, cx + outer_w / 2, height),
            fill=outer,
        )
        draw.rectangle(
            (0, cy - outer_h / 2, width, cy + outer_h / 2),
            fill=outer,
        )

        if inner:
            inner_w = max(3, outer_w // 2)
            inner_h = max(3, outer_h // 2)

            draw.rectangle(
                (cx - inner_w / 2, 0, cx + inner_w / 2, height),
                fill=inner,
            )
            draw.rectangle(
                (0, cy - inner_h / 2, width, cy + inner_h / 2),
                fill=inner,
            )

    def star(cx, cy, radius, color, points=5):
        coords = []

        for i in range(points * 2):
            angle = -math.pi / 2 + i * math.pi / points
            r = radius if i % 2 == 0 else radius * 0.42

            coords.append(
                (
                    cx + r * math.cos(angle),
                    cy + r * math.sin(angle),
                )
            )

        draw.polygon(coords, fill=color)

    if team_name == "Argentina":
        horizontal(["#75aadb", "#ffffff", "#75aadb"])
        draw.ellipse((31, 18, 41, 28), fill="#f6b40e")

    elif team_name == "Brazil":
        draw.rectangle((0, 0, width, height), fill="#009b3a")
        draw.polygon(
            [(36, 4), (66, 24), (36, 44), (6, 24)],
            fill="#ffdf00",
        )
        draw.ellipse((24, 12, 48, 36), fill="#002776")

    elif team_name == "France":
        vertical(["#0055a4", "#ffffff", "#ef4135"])

    elif team_name == "Germany":
        horizontal(["#000000", "#dd0000", "#ffce00"])

    elif team_name == "Spain":
        horizontal(["#aa151b", "#f1bf00", "#aa151b"], [1, 2, 1])

    elif team_name == "England":
        cross("#ffffff", "#ce1126")

    elif team_name == "Portugal":
        vertical(["#046a38", "#da291c"], [2, 3])

    elif team_name == "Netherlands":
        horizontal(["#ae1c28", "#ffffff", "#21468b"])

    elif team_name == "Belgium":
        vertical(["#111111", "#ffd90c", "#ef3340"])

    elif team_name == "Sweden":
        cross("#006aa7", "#fecc02")

    elif team_name == "Norway":
        cross("#ba0c2f", "#ffffff", "#00205b")

    elif team_name == "Switzerland":
        draw.rectangle((0, 0, width, height), fill="#d52b1e")
        draw.rectangle((30, 10, 42, 38), fill="white")
        draw.rectangle((22, 18, 50, 30), fill="white")

    elif team_name == "Türkiye":
        draw.rectangle((0, 0, width, height), fill="#e30a17")
        draw.ellipse((18, 10, 44, 38), fill="white")
        draw.ellipse((24, 12, 47, 36), fill="#e30a17")
        star(50, 24, 6, "white")

    elif team_name == "USA":
        stripe_h = height / 13

        for i in range(13):
            color = "#b22234" if i % 2 == 0 else "white"
            draw.rectangle(
                (
                    0,
                    round(i * stripe_h),
                    width,
                    round((i + 1) * stripe_h),
                ),
                fill=color,
            )

        draw.rectangle((0, 0, 30, 25), fill="#3c3b6e")

    elif team_name == "Japan":
        draw.rectangle((0, 0, width, height), fill="white")
        draw.ellipse((25, 13, 47, 35), fill="#bc002d")

    elif team_name == "South Korea":
        draw.rectangle((0, 0, width, height), fill="white")
        draw.pieslice((25, 13, 47, 35), 180, 360, fill="#cd2e3a")
        draw.pieslice((25, 13, 47, 35), 0, 180, fill="#0047a0")

    elif team_name == "Iran":
        horizontal(["#239f40", "#ffffff", "#da0000"])

    elif team_name == "Mexico":
        vertical(["#006847", "#ffffff", "#ce1126"])

    elif team_name == "Morocco":
        draw.rectangle((0, 0, width, height), fill="#c1272d")
        star(36, 24, 10, "#006233")

    elif team_name == "Senegal":
        vertical(["#00853f", "#fdef42", "#e31b23"])
        star(36, 24, 7, "#00853f")

    elif team_name == "Colombia":
        horizontal(["#fcd116", "#003893", "#ce1126"], [2, 1, 1])

    elif team_name == "Paraguay":
        horizontal(["#d52b1e", "#ffffff", "#0038a8"])

    elif team_name == "Canada":
        vertical(["#d52b1e", "#ffffff", "#d52b1e"], [1, 2, 1])
        star(36, 24, 9, "#d52b1e", points=7)

    elif team_name == "Algeria":
        vertical(["#006233", "#ffffff"])

    elif team_name == "Egypt":
        horizontal(["#ce1126", "#ffffff", "#000000"])

    elif team_name == "Côte d'Ivoire":
        vertical(["#f77f00", "#ffffff", "#009e60"])

    elif team_name == "Cabo Verde":
        draw.rectangle((0, 0, width, height), fill="#003893")
        draw.rectangle((0, 28, width, 34), fill="white")
        draw.rectangle((0, 35, width, 40), fill="#cf2027")

    elif team_name == "Curaçao":
        draw.rectangle((0, 0, width, height), fill="#002b7f")
        draw.rectangle((0, 31, width, 37), fill="#f9e300")

    elif team_name == "New Zealand":
        draw.rectangle((0, 0, width, height), fill="#00247d")

    elif team_name == "Bosnia & Herzegovina":
        draw.rectangle((0, 0, width, height), fill="#002395")
        draw.polygon([(20, 0), (58, 0), (58, 48)], fill="#fecb00")

    else:
        draw.rectangle((0, 0, width, height), fill="#d9d9d9")

    draw.rectangle(
        (0, 0, width - 1, height - 1),
        outline="#ffffff",
        width=1,
    )

    return image


def add_flag_icon(
    ax,
    team_name: str,
    x: float,
    y: float,
    zoom: float = 0.18,
):
    image_box = OffsetImage(
        make_flag_image(team_name),
        zoom=zoom,
    )

    annotation = AnnotationBbox(
        image_box,
        (x, y),
        frameon=True,
        pad=0.05,
        bboxprops=dict(
            boxstyle="round,pad=0.03",
            edgecolor="#ffffff",
            facecolor="#10271d",
            linewidth=0.7,
        ),
        zorder=10,
    )

    ax.add_artist(annotation)


# ============================================================
# GERÇEK FUTBOL SAHASI ORANI: 68 x 105
# ============================================================

def draw_vertical_pitch(ax):
    """
    Dikey kullanılan, 68 x 105 oranlı futbol sahası.
    Kare görünüm sorununu çözer.
    """

    width = 68
    height = 105

    ax.set_xlim(-2, width + 2)
    ax.set_ylim(-2, height + 2)
    ax.set_aspect("equal")
    ax.axis("off")

    stripe_colors = ["#0d6d40", "#0a6339"]

    for index in range(10):
        ax.add_patch(
            Rectangle(
                (0, index * height / 10),
                width,
                height / 10,
                color=stripe_colors[index % 2],
                zorder=0,
            )
        )

    line_color = "#effaf3"

    ax.add_patch(
        Rectangle(
            (0, 0),
            width,
            height,
            fill=False,
            linewidth=2.2,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.plot(
        [0, width],
        [height / 2, height / 2],
        color=line_color,
        linewidth=1.7,
        zorder=2,
    )

    ax.add_patch(
        Circle(
            (width / 2, height / 2),
            9.15,
            fill=False,
            linewidth=1.7,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Circle(
            (width / 2, height / 2),
            0.5,
            color=line_color,
            zorder=2,
        )
    )

    # Alt ceza sahası
    ax.add_patch(
        Rectangle(
            ((width - 40.3) / 2, 0),
            40.3,
            16.5,
            fill=False,
            linewidth=1.6,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Rectangle(
            ((width - 18.3) / 2, 0),
            18.3,
            5.5,
            fill=False,
            linewidth=1.6,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Circle(
            (width / 2, 11),
            0.45,
            color=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Arc(
            (width / 2, 11),
            18.3,
            18.3,
            theta1=37,
            theta2=143,
            linewidth=1.4,
            edgecolor=line_color,
            zorder=2,
        )
    )

    # Üst ceza sahası
    ax.add_patch(
        Rectangle(
            ((width - 40.3) / 2, height - 16.5),
            40.3,
            16.5,
            fill=False,
            linewidth=1.6,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Rectangle(
            ((width - 18.3) / 2, height - 5.5),
            18.3,
            5.5,
            fill=False,
            linewidth=1.6,
            edgecolor=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Circle(
            (width / 2, height - 11),
            0.45,
            color=line_color,
            zorder=2,
        )
    )

    ax.add_patch(
        Arc(
            (width / 2, height - 11),
            18.3,
            18.3,
            theta1=217,
            theta2=323,
            linewidth=1.4,
            edgecolor=line_color,
            zorder=2,
        )
    )


# ============================================================
# SAHA ÜZERİNDE MİNİMAL OYUNCU ETİKETLERİ
# ============================================================

def draw_pitch_player(
    ax,
    row: pd.Series,
    formation_name: str,
):
    position = str(row["position"])
    style = POSITION_STYLE[position]

    x, y = get_player_coordinates(
        formation_name,
        str(row["formation_slot"]),
    )

    rating = float(row["rating"])
    player_name = shorten_name(row["player_name"], 15)

    ax.scatter(
        [x],
        [y],
        s=1150,
        color=style["face"],
        edgecolor="#ffffff",
        linewidth=2.2,
        zorder=7,
    )

    ax.text(
        x,
        y,
        str(row["formation_slot"]),
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#07150e",
        zorder=8,
    )

    # Saha üzerinde yalnızca ad + rating.
    # Büyük detay kartları sağ panele taşındı.
    label_y = y - 6.0 if position != "G" else y + 5.0

    ax.text(
        x,
        label_y,
        f"{player_name}\n{rating:.1f}",
        ha="center",
        va="center",
        fontsize=7.7,
        color="white",
        fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.28",
            facecolor="#071b12",
            edgecolor=style["face"],
            linewidth=1.0,
            alpha=0.95,
        ),
        zorder=6,
    )


# ============================================================
# SAĞ DETAY PANELİ
# ============================================================

def draw_detail_panel(
    ax,
    formation_df: pd.DataFrame,
):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#081c13")

    ax.text(
        0.05,
        0.965,
        "OYUNCU DETAYLARI",
        color="white",
        fontsize=17,
        fontweight="bold",
        va="top",
    )

    ax.plot(
        [0.05, 0.95],
        [0.93, 0.93],
        color="#3f7557",
        linewidth=1.2,
    )

    ordered = formation_df.sort_values(
        ["position_order", "formation_slot"]
    ).reset_index(drop=True)

    top_y = 0.89
    row_height = 0.08

    for index, row in ordered.iterrows():
        y = top_y - index * row_height

        position = str(row["position"])
        style = POSITION_STYLE[position]

        team_name = str(row["national_team_name"])
        opponent = str(row["opponent_team_name"])

        player_name = shorten_name(row["player_name"], 24)
        code = team_code(team_name)

        rating = float(row["rating"])
        minutes = float(row["minutes_played"])
        goals = int(row["goals"]) if pd.notna(row["goals"]) else 0
        assists = int(row["assists"]) if pd.notna(row["assists"]) else 0
        xg = float(row["xg"]) if pd.notna(row["xg"]) else 0.0
        xa = float(row["xa"]) if pd.notna(row["xa"]) else 0.0

        # Kart arka planı
        ax.add_patch(
            Rectangle(
                (0.04, y - 0.075),
                0.92,
                0.086,
                facecolor="#0e291c",
                edgecolor=style["face"],
                linewidth=1.0,
                zorder=1,
            )
        )

        add_flag_icon(
            ax,
            team_name,
            0.095,
            y - 0.022,
            zoom=0.145,
        )

        ax.text(
            0.16,
            y,
            f"{row['formation_slot']}  {player_name}",
            color="white",
            fontsize=9.8,
            fontweight="bold",
            va="top",
            zorder=3,
        )

        ax.text(
            0.16,
            y - 0.027,
            (
                f"{code}  |  vs {opponent}  |  "
                f"Dak {minutes:.0f}"
            ),
            color="#b9d5c3",
            fontsize=7.6,
            va="top",
            zorder=3,
        )

        ax.text(
            0.16,
            y - 0.048,
            (
                f"G {goals}   A {assists}   "
                f"xG {xg:.2f}   xA {xa:.2f}"
            ),
            color="#8ebaa0",
            fontsize=7.2,
            va="top",
            zorder=3,
        )

        ax.text(
            0.91,
            y - 0.018,
            f"{rating:.1f}",
            color=style["face"],
            fontsize=15,
            fontweight="bold",
            ha="right",
            va="center",
            zorder=3,
        )


# ============================================================
# ANA GÖRSEL
# ============================================================

def create_single_image(
    stage_label: str,
    formation_name: str,
    formation_df: pd.DataFrame,
    save_path: Path,
):
    fig = plt.figure(figsize=FIGSIZE)
    fig.patch.set_facecolor("#061911")

    grid = GridSpec(
        1,
        2,
        figure=fig,
        width_ratios=[1.15, 0.85],
        wspace=0.04,
    )

    pitch_ax = fig.add_subplot(grid[0, 0])
    detail_ax = fig.add_subplot(grid[0, 1])

    draw_vertical_pitch(pitch_ax)

    for _, row in formation_df.iterrows():
        draw_pitch_player(
            pitch_ax,
            row,
            formation_name,
        )

    draw_detail_panel(
        detail_ax,
        formation_df,
    )

    average_rating = formation_df["rating"].mean()
    total_goals = formation_df["goals"].fillna(0).sum()
    total_assists = formation_df["assists"].fillna(0).sum()
    total_xg = formation_df["xg"].fillna(0).sum()
    total_xa = formation_df["xa"].fillna(0).sum()

    # Türkçe karakterler kaynak dosya kodlamasından etkilenmesin diye
    # Unicode kaçışları kullanıldı.
    title = (
        f"{stage_label} | "
        f"Haftan\u0131n Tak\u0131m\u0131 | "
        f"{formation_name}"
    )

    subtitle = (
        f"Ort. Rating {average_rating:.2f}"
        f"   |   G {total_goals:.0f}"
        f"   |   A {total_assists:.0f}"
        f"   |   xG {total_xg:.2f}"
        f"   |   xA {total_xa:.2f}"
    )

    fig.suptitle(
        title,
        color="white",
        fontsize=23,
        fontweight="bold",
        y=0.975,
    )

    fig.text(
        0.5,
        0.935,
        subtitle,
        ha="center",
        color="#bcdac7",
        fontsize=11.5,
    )

    fig.text(
        0.185,
        0.026,
        "GK",
        color=POSITION_STYLE["G"]["face"],
        fontsize=10,
        fontweight="bold",
    )

    fig.text(
        0.245,
        0.026,
        "DEF",
        color=POSITION_STYLE["D"]["face"],
        fontsize=10,
        fontweight="bold",
    )

    fig.text(
        0.305,
        0.026,
        "MID",
        color=POSITION_STYLE["M"]["face"],
        fontsize=10,
        fontweight="bold",
    )

    fig.text(
        0.365,
        0.026,
        "FWD",
        color=POSITION_STYLE["F"]["face"],
        fontsize=10,
        fontweight="bold",
    )

    plt.subplots_adjust(
        left=0.025,
        right=0.98,
        top=0.905,
        bottom=0.055,
    )

    fig.savefig(
        save_path,
        dpi=DPI,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
    )

    plt.close(fig)


# ============================================================
# PDF VE OVERVIEW
# ============================================================

def build_pdf(
    image_paths: list[Path],
    pdf_path: Path,
):
    valid_paths = [
        path for path in image_paths
        if path.exists()
    ]

    if not valid_paths:
        return

    images = [
        Image.open(path).convert("RGB")
        for path in valid_paths
    ]

    images[0].save(
        pdf_path,
        save_all=True,
        append_images=images[1:],
        resolution=150.0,
    )


def create_stage_overview(
    stage_label: str,
    image_paths: list[Path],
    save_path: Path,
):
    images = [
        Image.open(path).convert("RGB")
        for path in image_paths
        if path.exists()
    ]

    if not images:
        return

    thumbs = []

    for image in images:
        thumb = ImageOps.contain(
            image,
            (1050, 650),
        )

        frame = Image.new(
            "RGB",
            (thumb.width + 20, thumb.height + 20),
            (7, 22, 14),
        )

        frame.paste(
            thumb,
            (10, 10),
        )

        thumbs.append(frame)

    columns = 2
    rows = math.ceil(len(thumbs) / columns)

    card_width = max(image.width for image in thumbs)
    card_height = max(image.height for image in thumbs)

    header_height = 120

    canvas = Image.new(
        "RGB",
        (
            columns * card_width + 50,
            rows * card_height + header_height + 30,
        ),
        (5, 17, 11),
    )

    draw = ImageDraw.Draw(canvas)

    # Türkçe karakter bozulmasını önlemek için ASCII başlık.
    draw.text(
        (25, 24),
        f"{stage_label} | Tum Formasyonlar",
        fill=(245, 245, 245),
    )

    draw.text(
        (25, 65),
        f"Toplam {len(thumbs)} dizilim",
        fill=(175, 215, 190),
    )

    for index, image in enumerate(thumbs):
        row = index // columns
        column = index % columns

        canvas.paste(
            image,
            (
                15 + column * card_width,
                header_height + row * card_height,
            ),
        )

    canvas.save(save_path)

    canvas.save(
        save_path.with_suffix(".pdf"),
        "PDF",
        resolution=150.0,
    )


# ============================================================
# PROGRAM
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "../data/processed/weekly_team_analysis/teams_by_formation.csv"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "../docs/images/formation_visuals_v3"
        ),
    )

    parser.add_argument(
        "--stage-order",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--stage-label",
        type=str,
        default=None,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    individual_dir = args.output / "individual"
    overview_dir = args.output / "stage_overviews"

    individual_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    overview_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(
        args.input,
        low_memory=False,
    )

    numeric_columns = [
        "stage_order",
        "minutes_played",
        "rating",
        "goals",
        "assists",
        "xg",
        "xa",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if args.stage_order is not None:
        df = df[
            df["stage_order"].eq(args.stage_order)
        ].copy()

    if args.stage_label:
        df = df[
            df["stage_label"].eq(args.stage_label)
        ].copy()

    if df.empty:
        raise ValueError(
            "Secilen filtrelere uygun veri bulunamadi."
        )

    df = df.sort_values(
        [
            "stage_order",
            "formation",
            "position_order",
            "formation_slot",
        ]
    )

    all_images = []
    stage_images = {}

    for (
        stage_order,
        stage_label,
        formation_name,
    ), group in df.groupby(
        [
            "stage_order",
            "stage_label",
            "formation",
        ],
        sort=True,
    ):
        filename = (
            f"{int(stage_order):02d}_"
            f"{safe_filename(stage_label)}_"
            f"{safe_filename(formation_name)}.png"
        )

        save_path = individual_dir / filename

        create_single_image(
            stage_label,
            formation_name,
            group,
            save_path,
        )

        all_images.append(save_path)
        stage_images.setdefault(
            stage_label,
            [],
        ).append(save_path)

        print(f"Olusturuldu: {save_path}")

    build_pdf(
        all_images,
        args.output / "all_formations_report.pdf",
    )

    for stage_label, paths in stage_images.items():
        create_stage_overview(
            stage_label,
            paths,
            overview_dir
            / f"{safe_filename(stage_label)}_overview.png",
        )

        build_pdf(
            paths,
            args.output
            / f"{safe_filename(stage_label)}_report.pdf",
        )

    zip_path = (
        args.output.parent
        / f"{args.output.name}.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for file_path in sorted(
            args.output.rglob("*")
        ):
            if file_path.is_file():
                archive.write(
                    file_path,
                    arcname=file_path.relative_to(
                        args.output
                    ),
                )

    print()
    print(f"Toplam gorsel: {len(all_images)}")
    print(f"Cikti klasoru: {args.output}")
    print(
        f"Tek PDF: "
        f"{args.output / 'all_formations_report.pdf'}"
    )
    print(f"ZIP: {zip_path}")


if __name__ == "__main__":
    main()
