# FloatCam

A tiny, free, cross-platform floating webcam bubble. No menubar, no chrome — just your face in a draggable, resizable bubble, always on top. Works the same way on macOS, Windows, and Linux.

## Why

You want to record a demo or walkthrough with a screen recorder and show your face too — but you don't want to buy software. Run FloatCam, start your screen recording, done.

## Use cases

- Screen recordings with a face cam overlay
- Demo videos with a personal touch
- Loom-style recordings without Loom
- Livestreaming setups where you need a floating camera preview
- Video calls where you want to see how you look on a second display

## Install

Requires Python 3.8+ and a webcam.

```bash
git clone https://github.com/cagatay384/floatcam.git
cd floatcam
pip3 install -r requirements.txt
python3 floatcam.py
```

## Controls

- **Drag**: left click + drag the bubble to move it
- **Resize**: scroll the mouse wheel over the bubble
- **Right-click menu**:
  - **Size** — pick a preset (Small / Medium / Large / Extra Large)
  - **Shape** — Circle, Square, Rounded Square, Hexagon
  - **Border Color** — preset colors or a custom color picker
  - **Quit FloatCam**
- `Ctrl+Q` (or `Cmd+Q` on macOS): quit

Your shape, color, and size preferences are remembered between launches.

## Requirements

- Python 3.8+
- [PyQt5](https://pypi.org/project/PyQt5/)
- [opencv-python](https://pypi.org/project/opencv-python/)
- A camera

## License

MIT
