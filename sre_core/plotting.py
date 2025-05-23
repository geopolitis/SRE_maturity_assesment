import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

def plot_radar(ax, labels, values, label=None, y_max=5):
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    vals = values + values[:1]
    ax.plot(angles, vals, label=label)
    ax.fill(angles, vals, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, y_max)

def figure_to_image(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return Image.open(buf), buf
