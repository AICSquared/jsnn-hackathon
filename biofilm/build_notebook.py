"""Fill the TODO cells of the biofilm starter notebook and write biofilm_dispersion.ipynb.

Usage (from biofilm/):
    python build_notebook.py
    jupyter nbconvert --to notebook --execute --inplace biofilm_dispersion.ipynb
The starter's markdown and grading cells are kept unchanged; only TODO code cells are replaced.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / 'biofilm_dispersion_starter.ipynb'
DST = HERE / 'biofilm_dispersion.ipynb'

COLAB = '''# Colab: upload biofilm.zip, colony_masks.npz and breakup_scores.csv next to this notebook
# (Files panel), or mount Drive and put them in MyDrive/biofilm. Locally nothing is needed.
import importlib.util, subprocess, sys
if importlib.util.find_spec('tifffile') is None:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'tifffile'], check=True)
'''

CELLS = {}

CELLS[1] = COLAB + '''
from pathlib import Path
import io, zipfile
import numpy as np
import pandas as pd
import tifffile
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import display, Image as NotebookImage
DATA = Path.cwd()
if not (DATA / 'biofilm.zip').exists() and Path('/content/drive/MyDrive/biofilm/biofilm.zip').exists():
    DATA = Path('/content/drive/MyDrive/biofilm')  # optional Drive location
OUTPUT = DATA / 'submission'
OUTPUT.mkdir(exist_ok=True)
with zipfile.ZipFile(DATA / 'biofilm.zip') as archive:
    names = sorted(archive.namelist())
print('Images:', names[:3], '...')
'''

CELLS[3] = '''with zipfile.ZipFile(DATA / 'biofilm.zip') as archive:
    first_image = tifffile.imread(io.BytesIO(archive.read(names[0])))
plt.imshow(first_image, cmap='gray'); plt.title('First image'); plt.show()

frame_to_show = 8
with zipfile.ZipFile(DATA / 'biofilm.zip') as archive:
    another_image = tifffile.imread(io.BytesIO(archive.read(f'biofilm/frame_{frame_to_show:03d}.tif')))
print('Image shape (rows y, columns x):', another_image.shape, another_image.dtype)
plt.imshow(another_image, cmap='gray'); plt.title(f'Frame {frame_to_show}'); plt.show()
'''

CELLS[5] = '''with np.load(DATA / 'colony_masks.npz', allow_pickle=False) as archive:
    print('Available fields:', archive.files)
    filenames = archive['image_filenames'].copy()
    colony_ids = archive['colony_ids'].copy()
    masks = archive['masks'].copy()
assert masks is not None, 'Load masks before continuing'
with zipfile.ZipFile(DATA / 'biofilm.zip') as archive:
    images = np.stack([tifffile.imread(io.BytesIO(archive.read('biofilm/' + str(name)))) for name in filenames])
assert images.shape == masks.shape
print('Frames, rows, cols:', masks.shape, '| colonies:', colony_ids.tolist())

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
axes[0].imshow(images[frame_to_show], cmap='gray'); axes[0].set_title(f'Raw frame {frame_to_show}')
axes[1].imshow(images[frame_to_show], cmap='gray')
overlay = np.ma.masked_equal(masks[frame_to_show], 0)
axes[1].imshow(overlay, cmap='tab20', alpha=0.45, interpolation='nearest')
for ident in colony_ids:
    axes[1].contour(masks[frame_to_show] == ident, levels=[0.5], colors='yellow', linewidths=0.6)
    yy, xx = np.nonzero(masks[frame_to_show] == ident)
    if len(xx):
        axes[1].text(xx.mean(), yy.mean(), str(int(ident)), color='white', fontsize=9, ha='center', va='center')
axes[1].set_title(f'Frame {frame_to_show} with colony territory masks')
for ax in axes:
    ax.set(xlabel='x (pixels)', ylabel='y (pixels)')
fig.tight_layout(); plt.show()
'''

CELLS[7] = '''example_id = int(colony_ids[0])
yy, xx = np.nonzero(masks[0] == example_id)
example_x, example_y = xx.mean(), yy.mean()
print(example_id, example_x, example_y)
plt.imshow(images[0], cmap='gray')
plt.plot(example_x, example_y, 'r+')
plt.show()

second_id = int(colony_ids[1])
yy2, xx2 = np.nonzero(masks[0] == second_id)
second_x, second_y = xx2.mean(), yy2.mean()
print(second_id, second_x, second_y)
plt.imshow(images[0], cmap='gray')
plt.plot(example_x, example_y, 'r+', markersize=12, label=f'colony {example_id}')
plt.plot(second_x, second_y, 'c+', markersize=12, label=f'colony {second_id}')
plt.legend(); plt.title('Frame 0 territory centroids'); plt.show()
'''

CELLS[9] = '''def measure_centroids(masks, colony_ids):
    rows = []
    for ident in colony_ids:
        for frame in range(len(masks)):
            yy, xx = np.nonzero(masks[frame] == ident)
            if len(xx):
                x, y = xx.mean(), yy.mean()
            else:
                x, y = np.nan, np.nan  # absent observation: keep NaN, never 0
            rows.append({'colony_id': int(ident), 'frame': frame,
                         'centroid_x_px': float(x), 'centroid_y_px': float(y)})
    return pd.DataFrame(rows, columns=['colony_id', 'frame', 'centroid_x_px', 'centroid_y_px'])

centroids = measure_centroids(masks, colony_ids)
assert len(centroids) == len(masks) * len(colony_ids)
example = centroids[(centroids.colony_id == example_id) & (centroids.frame == 0)].iloc[0]
assert np.isclose(example.centroid_x_px, example_x)
assert np.isclose(example.centroid_y_px, example_y)
print('Absent observations:', int(centroids.centroid_x_px.isna().sum()))
centroids.head()
'''

CELLS[11] = '''def calculate_movement(centroids):
    out = []
    for ident, track in centroids.groupby('colony_id', sort=True):
        track = track.sort_values('frame').copy()
        disp, step, cum = [], [], []
        start = None      # first observed centroid
        prev = None       # (frame, x, y) of the previous observed frame
        total = 0.0
        for frame, x, y in zip(track.frame, track.centroid_x_px, track.centroid_y_px):
            if not (np.isfinite(x) and np.isfinite(y)):
                disp.append(np.nan); step.append(np.nan); cum.append(np.nan)
                continue
            if start is None:
                start = (x, y)
                s = 0.0 if frame == 0 else np.nan
            elif prev[0] == frame - 1:
                s = float(np.hypot(x - prev[1], y - prev[2]))
            else:
                s = np.nan  # gap: no step across missing frames
            if np.isfinite(s):
                total += s
            disp.append(float(np.hypot(x - start[0], y - start[1])))
            step.append(s)
            cum.append(total)
            prev = (frame, x, y)
        track['displacement_px'] = disp
        track['step_distance_px'] = step
        track['cumulative_distance_px'] = cum
        out.append(track)
    return pd.concat(out, ignore_index=True)

# Worked example: (0,0), (3,4), (3,0) -> displacement 0,5,3; cumulative 0,5,9.
_check = calculate_movement(pd.DataFrame({'colony_id': 1, 'frame': [0, 1, 2],
                                          'centroid_x_px': [0., 3., 3.], 'centroid_y_px': [0., 4., 0.]}))
assert np.allclose(_check.displacement_px, [0, 5, 3]) and np.allclose(_check.cumulative_distance_px, [0, 5, 9])
# Gap rules: first seen at frame 1 -> step NaN; absent frame -> all NaN; resume the total without a step across the gap.
_gap = calculate_movement(pd.DataFrame({'colony_id': 1, 'frame': [0, 1, 2, 3, 4],
                                        'centroid_x_px': [np.nan, 0., 3., np.nan, 3.],
                                        'centroid_y_px': [np.nan, 0., 4., np.nan, 0.]}))
assert np.allclose(_gap.cumulative_distance_px, [np.nan, 0, 5, np.nan, 5], equal_nan=True)
assert np.allclose(_gap.step_distance_px, [np.nan, np.nan, 5, np.nan, np.nan], equal_nan=True)
assert np.allclose(_gap.displacement_px, [np.nan, 0, 5, np.nan, 3], equal_nan=True)

movement = calculate_movement(centroids)
movement.head()
'''

CELLS[13] = '''THRESHOLD = 40.0
scores = pd.read_csv(DATA / 'breakup_scores.csv')
display(scores.head())

def analyze_breakup(scores, threshold):
    scored, crossings = [], []
    for ident, track in scores.groupby('colony_id', sort=True):
        track = track.sort_values('frame').copy()
        finite = track[np.isfinite(track.breakup_score)]
        first = finite.breakup_score.iloc[0] if len(finite) else np.nan
        track['breakup_change'] = track.breakup_score - first  # NaN scores stay NaN
        crossed = finite[finite.breakup_score >= threshold]
        crossings.append({'colony_id': int(ident),
                          'first_threshold_frame': float(crossed.frame.iloc[0]) if len(crossed) else np.nan})
        scored.append(track)
    scored = pd.concat(scored, ignore_index=True)
    crossings = pd.DataFrame(crossings, columns=['colony_id', 'first_threshold_frame'])
    return scored, crossings

scored_frames, crossings = analyze_breakup(scores, THRESHOLD)
display(crossings)
'''

CELLS[15] = '''frame_cols = ['colony_id', 'frame', 'centroid_x_px', 'centroid_y_px', 'displacement_px',
              'step_distance_px', 'cumulative_distance_px', 'breakup_score', 'breakup_change']
measurements = (movement.merge(scored_frames[['colony_id', 'frame', 'breakup_score', 'breakup_change']],
                               on=['colony_id', 'frame'], how='left')
                [frame_cols].sort_values(['colony_id', 'frame']).reset_index(drop=True))

def last_finite(series):
    finite = series[np.isfinite(series)]
    return float(finite.iloc[-1]) if len(finite) else np.nan

rows = []
for ident, track in measurements.groupby('colony_id', sort=True):
    track = track.sort_values('frame')
    observed = track.dropna(subset=['centroid_x_px', 'centroid_y_px'])
    finite_scores = track.breakup_score[np.isfinite(track.breakup_score)]
    rows.append({'colony_id': int(ident),
                 'final_displacement_px': float(observed.displacement_px.iloc[-1]) if len(observed) else np.nan,
                 'total_distance_px': last_finite(track.cumulative_distance_px),
                 'breakup_change': (float(finite_scores.iloc[-1] - finite_scores.iloc[0])
                                    if len(finite_scores) else np.nan)})
summary = pd.DataFrame(rows).merge(crossings, on='colony_id', how='left')
summary = summary[['colony_id', 'final_displacement_px', 'total_distance_px', 'breakup_change', 'first_threshold_frame']]

farthest = summary.loc[summary.final_displacement_px.idxmax()]
most_increase = summary.loc[summary.breakup_change.idxmax()]
print(f'Farthest from start: colony {int(farthest.colony_id)} ({farthest.final_displacement_px:.2f} px)')
print(f'Largest score increase: colony {int(most_increase.colony_id)} (+{most_increase.breakup_change:.1f})')
display(summary.round(3))
'''

PLOT = '''
display_trajectory_gif(images, measurements)

focus_id = int(most_increase.colony_id)
track = measurements[measurements.colony_id == focus_id].sort_values('frame')
cross = summary.loc[summary.colony_id == focus_id, 'first_threshold_frame'].iloc[0]
fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
top.plot(track.frame, track.displacement_px, 'o-', label='Displacement from first centroid')
top.plot(track.frame, track.cumulative_distance_px, 's--', label='Cumulative path distance')
top.set(ylabel='Distance (pixels)', title=f'Colony {focus_id}: movement and supplied breakup score')
top.legend(); top.grid(alpha=0.3)
bottom.plot(track.frame, track.breakup_score, 'o-', color='tab:purple', label='Supplied breakup score')
bottom.axhline(THRESHOLD, color='tab:red', linestyle=':', label=f'Threshold = {THRESHOLD:g}')
if pd.notna(cross):
    bottom.axvline(int(cross), color='tab:orange', linestyle='--', label=f'First crossing (frame {int(cross)})')
bottom.set(xlabel='Frame', ylabel='Breakup score (0-100)', ylim=(-2, 102))
bottom.legend(loc='upper left'); bottom.grid(alpha=0.3)
fig.tight_layout(); plt.show()
'''


def source_lines(text):
    lines = text.splitlines(keepends=True)
    if lines and lines[-1].endswith('\n'):
        lines[-1] = lines[-1][:-1]
    return lines


def main():
    nb = json.loads(SRC.read_text())
    cells = nb['cells']
    starter17 = ''.join(cells[17]['source'])
    helpers = starter17.split('# TODO: call display_trajectory_gif')[0].rstrip() + '\n'
    raw = "        ax.imshow(images[frame], cmap='gray')\n"
    assert helpers.count(raw) == 1, 'starter GIF helper changed; update the mask-overlay patch'
    # Brief item 5 asks for colony overlays in the GIF: draw each frame's territory masks over the raw image.
    helpers = helpers.replace(raw, raw + "        ax.imshow(np.ma.masked_equal(masks[frame], 0), cmap='tab20', "
                                         "alpha=0.35, interpolation='nearest')\n")
    CELLS[17] = helpers + PLOT
    for index, text in CELLS.items():
        assert cells[index]['cell_type'] == 'code', index
        cells[index]['source'] = source_lines(text)
        cells[index]['outputs'] = []
        cells[index]['execution_count'] = None
    interp_file = HERE / 'interpretation.md'
    if interp_file.exists():
        prompt = ''.join(cells[20]['source']).split('Write your response here.')[0].rstrip()
        cells[20]['source'] = source_lines(prompt + '\n\n### Interpretation\n\n' + interp_file.read_text())
    nb.setdefault('metadata', {})['kernelspec'] = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
    DST.write_text(json.dumps(nb, indent=1) + '\n')
    print('wrote', DST)


if __name__ == '__main__':
    main()
