from ontoagent.utils.inputs import InputSignalSpeech


def input_speech(input: dict) -> InputSignalSpeech:
    text = input["text"]
    speaker = input["speaker"]

    if isinstance(speaker, dict):
        speaker = None

    signal = InputSignalSpeech.build_from_text(text, speaker=speaker)

    if isinstance(input["speaker"], dict):
        agent = signal.root()["AGENT"].singleton()
        for key in input["speaker"].keys():
            agent[key] += input["speaker"][key]

    return signal
