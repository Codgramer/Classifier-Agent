import json
import datetime
import pdfplumber
from typing import Dict, Any, Optional
import logging
import re
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Shared memory (in-memory dictionary)
memory: Dict[str, Dict[str, Any]] = {}

def save_memory_to_file(thread_id: str):
    """Save memory to a JSON file for persistence."""
    try:
        with open('memory_log.json', 'w') as f:
            json.dump(memory, f, indent=2)
        logger.info(f"Memory saved to memory_log.json for thread {thread_id}")
    except Exception as e:
        logger.error(f"Failed to save memory: {str(e)}")

def read_file_content(file_path: str, format_type: str) -> str:
    """Read content from a file based on its format."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if format_type == 'pdf':
            if file_path.endswith('.txt'):  # Mock PDF as text for testing
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                with pdfplumber.open(file_path) as pdf:
                    content = ''.join([page.extract_text() or '' for page in pdf.pages])
            if not content:
                raise ValueError("No text extracted from PDF")
            return content
        elif format_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                return json.dumps(json_data)
        elif format_type == 'email':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        raise

def classify_intent(content: str, format_type: str, json_data: Optional[Dict] = None) -> str:
    """Classify the intent of the content using heuristics."""
    try:
        content_lower = content.lower()
        if format_type == 'json' and json_data:
            doc_type = json_data.get('DocDtls', {}).get('Typ', '')
            if doc_type == 'INV':
                return 'Invoice'
        if 'rfq' in content_lower or 'quote' in content_lower:
            intent = 'RFQ'
        elif 'invoice' in content_lower or 'inv' in content_lower:
            intent = 'Invoice'
        elif 'complaint' in content_lower or 'issue' in content_lower or 'damaged' in content_lower:
            intent = 'Complaint'
        elif 'regulation' in content_lower:
            intent = 'Regulation'
        else:
            intent = 'Other'
        logger.info(f"Classified intent: {intent}")
        return intent
    except Exception as e:
        logger.error(f"Intent classification failed: {str(e)}")
        return 'Other'

def extract_from_text(text: str, intent: str) -> Dict[str, Any]:
    """Extract specific information from text based on intent using heuristics."""
    try:
        extracted = {"urgency": "high" if "urgent" in text.lower() else "normal"}
        
        if intent == 'RFQ':
            quantity = re.search(r'(\d+)\s*units?', text, re.IGNORECASE)
            product = re.search(r'product\s*(\w+)', text, re.IGNORECASE)
            extracted.update({
                'quantity': int(quantity.group(1)) if quantity else 'N/A',
                'product': product.group(1) if product else 'N/A'
            })
        elif intent == 'Complaint':
            order_id = re.search(r'order\s*#?(\d+)', text, re.IGNORECASE)
            issue = re.search(r'(damaged|defective|wrong|issue)\s+([^\n.;]{1,50})', text, re.IGNORECASE)
            extracted.update({
                'order_id': order_id.group(1) if order_id else 'N/A',
                'issue': issue.group(0) if issue else 'N/A'
            })
        elif intent == 'Invoice':
            invoice_num = re.search(r'invoice\s*#?(\w+)', text, re.IGNORECASE) or re.search(r'no[\'":\s]+([\w\/]+)', text, re.IGNORECASE)
            total = re.search(r'total\s*\$?(\d+\.?\d*)', text, re.IGNORECASE) or re.search(r'totinvval[\'":\s]+(\d+\.?\d*)', text, re.IGNORECASE)
            extracted.update({
                'invoice_number': invoice_num.group(1) if invoice_num else 'N/A',
                'total': float(total.group(1)) if total else 'N/A'
            })
        else:
            name = re.search(r'^\s*([A-Za-z\s]+)\n', text, re.MULTILINE)
            email = re.search(r'[\w\.-]+@[\w\.-]+', text)
            phone = re.search(r'\+?\d{1,3}[-.\s]?\d{10}', text)
            summary = text[:200]
            extracted.update({
                'name': name.group(1).strip() if name else 'N/A',
                'email': email.group(0) if email else 'N/A',
                'phone': phone.group(0) if phone else 'N/A',
                'summary': summary
            })
        logger.info(f"Extracted info: {extracted}")
        return extracted
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return {"summary": text[:200], "urgency": "normal"}

class ClassifierAgent:
    def process_input(self, input_data: Dict[str, Any]) -> None:
        """Process input, classify format and intent, and route to appropriate agent."""
        try:
            format_type = input_data.get('format')
            file_path = input_data.get('file_path')
            sender = input_data.get('sender', 'unknown')
            thread_id = input_data.get('thread_id', f"thread_{datetime.datetime.now().timestamp()}")
            timestamp = input_data.get('timestamp', datetime.datetime.now().isoformat())

            # Initialize memory entry
            if thread_id not in memory:
                memory[thread_id] = {}
            memory[thread_id].update({
                'source': sender,
                'type': format_type,
                'timestamp': timestamp,
                'file_path': file_path,
                'logs': [f"Classifier: Detected {format_type} from {file_path}"]
            })

            # Read content from file
            content = read_file_content(file_path, format_type)

            if format_type == 'pdf':
                intent = classify_intent(content, format_type)
                memory[thread_id]['intent'] = intent
                memory[thread_id]['logs'].append(f"Classifier: Classified intent as {intent}")
                email_agent = EmailAgent()
                email_agent.process_text(content, thread_id, intent)
            elif format_type == 'json':
                try:
                    json_data = json.loads(content)
                    intent = classify_intent(content, format_type, json_data)
                    memory[thread_id]['intent'] = intent
                    memory[thread_id]['logs'].append(f"Classifier: Classified intent as {intent}")
                    json_agent = JSONAgent()
                    json_agent.process_json(json_data, thread_id, intent)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON format")
                    memory[thread_id]['logs'].append("Classifier: Invalid JSON format")
            elif format_type == 'email':
                intent = classify_intent(content, format_type)
                memory[thread_id]['intent'] = intent
                memory[thread_id]['logs'].append(f"Classifier: Classified intent as {intent}")
                email_agent = EmailAgent()
                email_agent.process_text(content, thread_id, intent)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            save_memory_to_file(thread_id)
        except Exception as e:
            logger.error(f"Classifier error: {str(e)}")
            memory[thread_id]['logs'].append(f"Classifier: Error: {str(e)}")
            save_memory_to_file(thread_id)

class JSONAgent:
    def process_json(self, json_data: Dict[str, Any], thread_id: str, intent: str) -> None:
        """Process JSON input and reformat based on intent."""
        try:
            if intent == 'Invoice':
                extracted_values = {
                    'invoice_number': json_data.get('DocDtls', {}).get('No', 'N/A'),
                    'date': json_data.get('DocDtls', {}).get('Dt', 'N/A'),
                    'total': json_data.get('ValDtls', {}).get('TotInvVal', 'N/A'),
                    'currency': 'INR' if json_data.get('ValDtls', {}).get('CgstVal') else 'N/A'
                }
                anomalies = [k for k, v in extracted_values.items() if v == 'N/A']
            elif intent == 'RFQ':
                extracted_values = {
                    'product': json_data.get('ItemList', [{}])[0].get('PrdDesc', 'N/A'),
                    'quantity': json_data.get('ItemList', [{}])[0].get('Qty', 'N/A'),
                    'delivery_date': json_data.get('DocDtls', {}).get('Dt', 'N/A')
                }
                anomalies = [k for k, v in extracted_values.items() if v == 'N/A']
            elif intent == 'Complaint':
                extracted_values = {
                    'order_id': json_data.get('DocDtls', {}).get('No', 'N/A'),
                    'issue': json_data.get('ItemList', [{}])[0].get('PrdDesc', 'N/A')
                }
                anomalies = [k for k, v in extracted_values.items() if v == 'N/A']
            else:
                extracted_values = {'data': json_data}
                anomalies = []
            memory[thread_id]['extracted_values'] = extracted_values
            memory[thread_id]['logs'].append(f"JSON Agent: Extracted values; Anomalies: {anomalies}")
            logger.info(f"JSON Agent processed thread {thread_id}: {extracted_values}")
        except Exception as e:
            logger.error(f"JSON Agent error: {str(e)}")
            memory[thread_id]['logs'].append(f"JSON Agent: Error: {str(e)}")

class EmailAgent:
    def process_text(self, text: str, thread_id: str, intent: str) -> None:
        """Process text input and extract information based on intent."""
        try:
            extracted_values = extract_from_text(text, intent)
            extracted_values['sender'] = memory[thread_id]['source']
            memory[thread_id]['extracted_values'] = extracted_values
            memory[thread_id]['logs'].append(f"Email Agent: Extracted info for {intent}")
            logger.info(f"Email Agent processed thread {thread_id}: {extracted_values}")
        except Exception as e:
            logger.error(f"Email Agent error: {str(e)}")
            memory[thread_id]['logs'].append(f"Email Agent: Error: {str(e)}")

# Example usage with file paths
if __name__ == "__main__":
    inputs = [
        {
            'format': 'email',
            'file_path': r"C:\Users\Himanshu\Downloads\email_rfq.txt",
            'sender': 'john.doe@example.com',
            'thread_id': 'thread_123',
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'format': 'email',
            'file_path': r"C:\Users\Himanshu\Downloads\email_complaint.txt",
            'sender': 'jane.smith@example.com',
            'thread_id': 'thread_124',
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'format': 'json',
            'file_path': r"C:\Users\Himanshu\Downloads\sales_invoice.json",
            'sender': 'system@example.com',
            'thread_id': 'thread_456',
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'format': 'json',
            'file_path': r"C:\Users\Himanshu\Downloads\service_invoice.json",
            'sender': 'system@example.com',
            'thread_id': 'thread_457',
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'format': 'pdf',
            'file_path': r"C:\Users\Himanshu\Downloads\complaint1.pdf",
            'sender': 'alice.brown@example.com',
            'thread_id': 'thread_789',
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'format': 'pdf',
            'file_path': r"C:\Users\Himanshu\Downloads\complaint2.pdf",
            'sender': 'bob.wilson@example.com',
            'thread_id': 'thread_790',
            'timestamp': datetime.datetime.now().isoformat()
        }
    ]

    classifier = ClassifierAgent()
    for input_data in inputs:
        logger.info(f"Processing input: {input_data['thread_id']} from {input_data['file_path']}")
        classifier.process_input(input_data)
    
    # Print memory for demonstration
    import pprint
    logger.info("Final memory state:")
    pprint.pprint(memory, indent=2)