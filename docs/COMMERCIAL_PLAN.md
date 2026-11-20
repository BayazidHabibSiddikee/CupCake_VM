# CupCake Robot: Commercial Product Architecture & Sales Platform Plan

This document outlines the end-to-end plan to transition CupCake from an Android-dependent prototype into a **standalone consumer desktop AI companion robot**, complete with a high-conversion e-commerce/pre-order website, cloud pipeline, and pay-as-you-go unit economics.

---

## 1. Executive Summary & Vision

* **What it is:** CupCake is a standalone, interactive chibi desktop robot with real physical expressions, motorized arm/head/leg gestures, OLED facial expressions, and bilingual (Bangla + English) conversational intelligence.
* **Target Audience:** Kids, anime/tech enthusiasts, desk workers seeking companionship, and students.
* **Key Pivot:** **No phone needed.** Powered directly on-device by an ESP32-S3 (with I2S mic + speaker + OLED + 3 servos) communicating directly over Wi-Fi with an ultra-low-cost, high-performance cloud pipeline.
* **Monetization:** 
  1. Hardware sale (e.g., 2,500 – 3,500 BDT DIY kit / 4,500 – 6,000 BDT assembled).
  2. Free tier allowance (e.g., 30 daily chats).
  3. "Snack Packs" / Monthly Subscription (e.g., 150 – 250 BDT / month for unlimited voice).

---

## 2. Hardware Architecture (Standalone ESP32-S3)

```mermaid
flowchart TD
    subgraph CupCake Hardware
        MIC["INMP441 I2S Mic\n(I2S_NUM_0)"] -->|PCM Stream| ESP["ESP32-S3\n(Dual Core + Wi-Fi)"]
        ESP -->|I2S_NUM_1| AMP["MAX98357A I2S Amp"] --> SPK["Mini Cavity Speaker"]
        ESP -->|I2C| OLED["SSD1306 0.96 OLED\n(Eyes & Expressions)"]
        ESP -->|PWM| SERVOS["3x Micro Servos\n(Arms + Waist)"]
        ESP -->|GPIO| BUTTONS["4x Belly Tactile Buttons"]
        BATT["3.7V Flat Li-ion (BL-5C)"] --> ESP
        FLASH["8MB On-Chip Flash\n(20+ Cached SFX/Yawns)"] --- ESP
    end

    subgraph Serverless Cloud Pipeline
        ESP -->|HTTP POST /stream| API["Vercel / Cloudflare Edge API"]
        API -->|Audio| STT["Groq Whisper-Large-v3-Turbo\n($0.04/hr)"]
        STT -->|Text| LLM["Gemini 2.5 Flash / Groq Llama-3-8B\n($0.05/1M tokens)"]
        LLM -->|Text + Tag| TTS["Gemini Flash TTS / DeepInfra Kokoro\n(Raw 16kHz PCM)"]
        TTS -->|PCM Audio + [emotion] Header| ESP
    end
```

### Pin Allocation on ESP32-S3
1. **I2S0 (Microphone Input):** INMP441 (BCLK, WS, SD)
2. **I2S1 (Speaker Audio Out):** MAX98357A (BCLK, LRC, DIN)
3. **I2C (Display):** SDA, SCL -> OLED SSD1306
4. **PWM (Servos):** Left Shoulder, Right Shoulder, Waist Swivel
5. **GPIO Inputs:** 4 Buttons + Battery Voltage ADC

---

## 3. Cloud Audio Pipeline & Pay-As-You-Go Economics

### Unit Economics Per Active Heavy User (50 turns/day = 1,500 interactions/mo):
| Component | Provider & Model | Monthly Cost per User |
|---|---|---|
| **STT (Speech-to-Text)** | Groq `whisper-large-v3-turbo` | ~$0.10 (2.5 hrs audio) |
| **LLM (Reasoning & Emotes)** | Gemini 2.5 Flash / Groq Llama-3-8B | ~$0.05 (1,500 short turns) |
| **TTS (Voice Synthesis)** | Gemini Flash-Lite TTS (Bangla/Eng) | ~$1.20 - $1.40 |
| **Local Cache Savings** | 20 Flash SFX (yawns, giggles, button sounds) | $0.00 (Offloads ~20% API calls) |
| **Total Monthly Server Cost** | | **~$1.35 - $1.55 / user** |

* **Selling "Snack Pack" Top-Up:** 250 BDT (~$2.20 USD) for 1,000 extra voice tokens.
* **Profit Margin:** **~50% to 65%** on cloud top-ups.

---

## 4. Sales & Commercial Website Architecture

A modern, high-converting e-commerce web platform hosted on **Vercel** with local payment support (bKash, Nagad, Cards):

### Key Website Sections
1. **Hero Section:**
   - Interactive 3D/Video preview of CupCake reacting to voice.
   - Core value proposition: "Your Chibi AI Companion on Your Desk. No phone required."
   - Primary Call to Action: **"Pre-order Now"** / **"Buy DIY Kit"**.
2. **Interactive Soundboard & Face Preview:**
   - Lets prospective buyers test CupCake's personality, sounds, and facial expressions in-browser.
3. **Features & Hardware Specs:**
   - Dual-language conversational brain (Banglish / English).
   - Movable arms & 360-tilt Reverse-T leg.
   - Built-in speaker, mic, and rechargeable battery.
4. **Editions & Pricing:**
   - **Hacker/DIY Kit:** 3D printed shells + ESP32-S3 + Servos + Speaker/Mic parts + Screws + Flash tutorial (~2,999 BDT / $27).
   - **Ready-to-Play Assembled Edition:** Fully assembled, calibrated, gift boxed (~4,999 BDT / $45).
5. **Pre-Order / Checkout Flow:**
   - Direct integration with local MFS (bKash / Nagad / Rocket) & Card checkout (via SSLCommerz, Shurjopay, or Stripe for international).
   - Instant order tracking.
6. **Parent & User Portal:**
   - Manage robot Wi-Fi settings, adjust personality (Cute, Tsundere, Study Buddy), and refill "Snack" credits.

---

## 5. Implementation Roadmap

- [ ] **Phase 1: Commercial Landing Page**
  - Create `web/` directory with lightweight, responsive Next.js / Tailwind or static single-page web app ready for free Vercel deployment.
  - Implement dynamic pre-order form, soundboard preview, and product gallery.
- [ ] **Phase 2: Unified Serverless Voice Endpoint (`/api/chat-voice`)**
  - Next.js / Edge Function receiving raw PCM or base64 audio from ESP32 -> Groq Whisper -> Gemini 2.5 Flash -> TTS -> Streaming 16kHz PCM back.
- [ ] **Phase 3: Firmware Boilerplate for ESP32-S3 Standalone**
  - Dual I2S setup (INMP441 mic on I2S0, MAX98357A on I2S1).
  - Wi-Fi manager portal for initial home setup.
- [ ] **Phase 4: Payment Gateway & Order Management**
  - Integrate bKash / Nagad webhook for automated order confirmation.
