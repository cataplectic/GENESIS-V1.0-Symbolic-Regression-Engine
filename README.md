# GENESIS: Uncovering the Mathematical Truth Hidden in Data 🌌

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-green)

Welcome to **GENESIS**. 

If you are tired of importing massive, black-box deep learning models just to understand the relationship between a few variables, you are in the right place. GENESIS is an evolutionary Symbolic Regression engine built from scratch. It doesn't just predict the future; it tells you exactly *how* it predicts it by giving you the raw mathematical equation.

## 📖 The Story Behind GENESIS

Machine learning today is obsessed with massive neural networks. But here is the reality: you can't easily deploy a billion-parameter transformer model onto an ESP32 microcontroller or a low-power sensor node. 

As an electrical-electronics engineering student, I constantly deal with the physical world—hardware, control systems, and raw sensor data. I realized that the industry doesn't always need a "black box" that guesses a temperature or a voltage. We need reliable, lightweight, and explainable physics. We need equations that can be hardcoded into C/C++ for edge devices, calculating results in microseconds without burning through battery life.

That is why I built GENESIS. I wanted an algorithm that looks at chaotic, noisy data and strips away the noise to find the fundamental laws of physics underneath—whether that's a partial aerodynamic drag formula, a battery degradation curve, or a sensor linearization equation.

## 🧠 What Does It Actually Do?

GENESIS takes a simple CSV file filled with numerical data and unleashes an evolutionary algorithm to breed mathematical formulas. 

It generates random abstract syntax trees (ASTs) containing operators like `+`, `-`, `*`, `/`, `sin`, `cos`, and `exp`. Through generations of mutation, crossover, and natural selection, it kills off the weak formulas and keeps the ones that best fit the data. 

Finally, it uses libraries like `sympy` to prune and simplify the winning tree into a beautiful, human-readable equation, while `scipy` fine-tunes the constants.

### Key Features
* **Zero Black Boxes (Explainable AI):** The output is a literal math equation. You know exactly what the model is doing.
* **Edge-AI Ready:** The formulas generated can be executed on the cheapest microcontrollers with zero overhead. No neural network frameworks required.
* **Autonomous Constant Optimization:** It doesn't just find the structure of the equation; it mathematically optimizes the coefficients for the lowest possible error.
* **Parsimony Pressure:** It actively penalizes overly long and complex equations to prevent overfitting and avoid "singularity traps" (like dividing by near-zero values).

## 🚀 Getting Started

You don't need a supercomputer to run this. Just a standard Python environment.

### 1. Installation
Clone the repository and install the dependencies:

```bash
git clone [https://github.com/yourusername/GENESIS.git](https://github.com/yourusername/GENESIS.git)
cd GENESIS
pip install -r requirements.txt
