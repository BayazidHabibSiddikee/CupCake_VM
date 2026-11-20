// Serverless Endpoint for Standalone ESP32-S3 Voice Processing
// Compatible with Vercel Serverless / Cloud Functions / Node.js
// Pipeline: ESP32 Audio (WAV/PCM) -> Groq Whisper (STT) -> Gemini Flash (LLM) -> Gemini / DeepInfra TTS -> ESP32

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed. Use POST.' });
  }

  try {
    const { audioBase64, textInput, userToken } = req.body || {};

    // 1. Verify User Quota / Token (Pay-As-You-Go Gatekeeper)
    // You can check userToken against Upstash Redis or Supabase table
    const remainingChats = 50; // Mock check

    let userPrompt = textInput;

    // 2. STT via Groq Whisper (if raw audio was sent from INMP441 mic)
    if (audioBase64 && !userPrompt) {
      const groqApiKey = process.env.GROQ_API_KEY;
      if (!groqApiKey) {
        throw new Error('GROQ_API_KEY environment variable is missing.');
      }

      // Convert base64 audio to binary buffer for Groq Whisper
      const audioBuffer = Buffer.from(audioBase64, 'base64');
      const formData = new FormData();
      const blob = new Blob([audioBuffer], { type: 'audio/wav' });
      formData.append('file', blob, 'speech.wav');
      formData.append('model', 'whisper-large-v3-turbo');
      formData.append('language', 'bn'); // Supports auto-detect or mixed Bengali/English

      const groqRes = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${groqApiKey}` },
        body: formData,
      });

      const groqData = await groqRes.json();
      userPrompt = groqData.text;
    }

    if (!userPrompt || userPrompt.trim() === '') {
      return res.status(400).json({ error: 'No speech or text detected.' });
    }

    // 3. Brain: Gemini 2.5 Flash / Groq Llama-3-8B (Super Cheap & Smart)
    const geminiApiKey = process.env.GEMINI_API_KEY;
    const systemInstruction = 
      "You are CupCake, an adorable, clingy, competitive chibi desk companion robot. " +
      "You speak fluent Banglish (casual conversational Bengali mixed with English). " +
      "Always start your response with an emotion tag in brackets like [happy], [sleepy], [angry], [wink], or [excited], " +
      "followed by 1-2 very short sentences (max 25 words). Keep it cute, playful, and expressive.";

    let replyText = "[happy] Shob thik ache! What are we building today?";
    let emotion = "happy";

    if (geminiApiKey) {
      const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_instruction: { parts: [{ text: systemInstruction }] },
          contents: [{ parts: [{ text: userPrompt }] }],
          generationConfig: { maxOutputTokens: 60, temperature: 0.7 }
        })
      });

      const geminiData = await geminiRes.json();
      const rawText = geminiData.candidates?.[0]?.content?.parts?.[0]?.text || replyText;
      
      // Parse [emotion] tag
      const match = rawText.match(/\[([a-zA-Z_]+)\]/);
      if (match) {
        emotion = match[1].toLowerCase();
      }
      replyText = rawText.replace(/\[[a-zA-Z_]+\]\s*/, '');
    }

    // 4. Set Headers for the Robot (So OLED face & servos animate before audio plays!)
    res.setHeader('X-CupCake-Emotion', emotion);
    res.setHeader('X-CupCake-Prompt', encodeURIComponent(userPrompt));
    res.setHeader('X-Remaining-Snacks', remainingChats);

    // 5. Return Clean JSON or Stream Audio
    // If client requested JSON:
    return res.status(200).json({
      emotion: emotion,
      replyText: replyText,
      userPrompt: userPrompt,
      remainingSnacks: remainingChats
    });

  } catch (err) {
    console.error('CupCake Voice API Error:', err);
    return res.status(500).json({ error: err.message });
  }
}
