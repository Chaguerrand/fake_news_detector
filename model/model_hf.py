from transformers import AutoTokenizer, DistilBertForSequenceClassification
import torch

HF_MODEL = "pekosmaggle/bert-fakenews"

def load_model_hf():
    model_hf = DistilBertForSequenceClassification.from_pretrained(HF_MODEL)
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model_hf.eval()
    return model_hf, tokenizer

def pred_hf(model_hf, tokenizer, text):
    inputs = tokenizer(
        text,
        max_length=256,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )

    with torch.no_grad():
        outputs = model_hf(**inputs)

    proba = torch.softmax(outputs.logits, dim=1)
    predicted = torch.argmax(proba, dim=1).item()
    confidence = round(proba[0][predicted].item(), 4)

    return {
        "label": "FAKE" if predicted == 1 else "REAL",
        "confidence": confidence
    }

if __name__ == "__main__":
    model_hf, tokenizer = load_model_hf()
    test = "Trump says the election was stolen"
    print(pred_hf(model_hf, tokenizer, test))
