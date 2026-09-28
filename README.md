# 🚀 Game Optimizer & Benchmark Suite

A high-performance Windows desktop utility built with `customtkinter` designed to analyze your PC hardware, run rigorous stress tests, and fetch live game requirements to generate custom, performance-tuned settings profiles.

---

## ⚖️ License & Usage Terms

> **Copyright (c) 2026 SomeGreeen. All rights reserved.**
> 
> This repository contains source code provided for **viewing purposes only**. 
> - **Strictly Prohibited:** Copying, modifying, creating derivative works, or redistributing this code without express written permission from the author.
> - If you wish to contribute, suggest changes, or report issues, please contact the author directly via GitHub or pull request discussions.

---

## ✨ Key Features

- **Live Game Requirements:** Fetches real-time system requirements from Steam and RAWG APIs.
- **Hardware Benchmarking Suite:** Aggressive, multi-threaded stress tests for:
  - **CPU:** Floating-point math matrix load (utilizes 100% of all logical cores).
  - **RAM:** Deep allocation and bandwidth test targeting up to 50% of available memory.
  - **Storage (NVMe/SSD):** Sequential Read/Write throughput checks.
  - **GPU:** 3D shader simulation using ModernGL.
- **Dynamic Optimization Matrix:** Side-by-side comparison of Performance, Balanced, and Maximum Ultra profiles.
- **Visual Report Export:** Generate and save clean, dark-themed `.png` report matrices of your optimization results.
- **Network Diagnostics:** Built-in speedometer (Bandwidth) and ping/jitter/packet loss checks against major gaming servers.

---

## 📥 Installation & Usage (For Users)

If you just want to run the application without installing Python:
1. Head over to the **[Releases](../../releases)** tab on GitHub.
2. Download the latest `GameOptimizer.exe`.
3. Double-click to run! (No installation required).

---

## 🛠️ Running from Source (For Developers / View-Only)

If you have Python installed and want to inspect the source code locally and run it:

1. Clone or download the repository.
2. Install the required dependencies in your terminal:
   ```bash
   pip install customtkinter requests pillow moderngl numpy
3. Run the application via Python by executing the main script:
   ```bash
   python main.py
