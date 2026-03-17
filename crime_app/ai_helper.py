# ai_helper.py
import re
import json

class CrimeAIAnalyzer:
    """
    Simple AI for crime report analysis
    No heavy ML libraries - works on PythonAnywhere!
    """
    
    PRIORITY_KEYWORDS = {
        'Emergency': {
            'words': [
                'gun', 'shooting', 'firearm', 'weapon', 'bleeding', 'dying',
                'fire', 'explosion', 'bomb', 'kidnap', 'hostage', 'terrorist',
                'murder', 'killing', 'death', 'critical', 'emergency', 'immediate',
                'ambulance', 'hospital', 'unconscious', 'heart attack', 'stroke'
            ],
            'weight': 3
        },
        'High': {
            'words': [
                'assault', 'robbery', 'stabbing', 'violence', 'threat', 'threatening',
                'fight', 'beating', 'attack', 'injured', 'wound', 'blood',
                'mugging', 'carjacking', 'break-in', 'home invasion',
                'domestic violence', 'abuse', 'harassment', 'stalking'
            ],
            'weight': 2
        },
        'Medium': {
            'words': [
                'theft', 'burglary', 'vandalism', 'fraud', 'scam', 'stolen',
                'missing', 'property damage', 'trespassing', 'suspicious',
                'disturbance', 'noise', 'complaint', 'disorderly', 'loitering',
                'shoplifting', 'pickpocket', 'purse snatching'
            ],
            'weight': 1
        },
        'Low': {
            'words': [
                'lost', 'found', 'information', 'inquiry', 'question',
                'report only', 'documentation', 'record', 'minor',
                'yesterday', 'last week', 'not urgent', 'non-emergency'
            ],
            'weight': 1
        }
    }
    
    INCIDENT_KEYWORDS = {
        'Robbery': ['robbery', 'mugging', 'held up', 'carjacking', 'armed robbery'],
        'Burglary': ['burglary', 'break-in', 'broke into', 'forced entry', 'home invasion'],
        'Theft': ['theft', 'stolen', 'shoplifting', 'pickpocket', 'purse snatching'],
        'Assault': ['assault', 'beating', 'attacked', 'hit', 'punched', 'fighting'],
        'Cybercrime': ['hack', 'phishing', 'online scam', 'cyber', 'internet fraud'],
        'Fraud': ['fraud', 'scam', 'fake', 'cheated', 'forgery'],
        'Vandalism': ['vandalism', 'graffiti', 'destroyed', 'damaged property'],
        'Domestic Violence': ['domestic', 'family', 'wife', 'husband', 'partner'],
        'Drug Offense': ['drug', 'narcotics', 'weed', 'cocaine', 'substance'],
        'Traffic Accident': ['accident', 'crash', 'collision', 'hit and run'],
        'Missing Person': ['missing', 'runaway', 'disappeared', 'vanished'],
        'Harassment': ['harassment', 'stalking', 'threatening', 'intimidation'],
        'Sexual Assault': ['rape', 'sexual assault', 'molestation', 'abuse'],
        'Other': []
    }
    
    @classmethod
    def analyze_priority(cls, title, description):
        """Analyze text to suggest priority level"""
        combined_text = f"{title} {description}".lower()
        scores = {'Emergency': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        matched_keywords = []
        
        for priority, data in cls.PRIORITY_KEYWORDS.items():
            for keyword in data['words']:
                if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                    scores[priority] += data['weight']
                    matched_keywords.append(keyword)
        
        # Find highest score
        max_score = 0
        suggested = 'Medium'
        for priority, score in scores.items():
            if score > max_score:
                max_score = score
                suggested = priority
        
        # Calculate confidence
        total = sum(scores.values())
        confidence = (max_score / total * 100) if total > 0 else 50
        
        return {
            'suggested_priority': suggested,
            'confidence': round(confidence, 1),
            'scores': scores,
            'matched_keywords': list(set(matched_keywords))[:10],
            'total_keywords_matched': len(set(matched_keywords))
        }
    
    @classmethod
    def analyze_incident_type(cls, description):
        """Analyze description to suggest incident type"""
        desc_lower = description.lower()
        matches = {}
        
        for incident, keywords in cls.INCIDENT_KEYWORDS.items():
            if not keywords:  # Skip 'Other'
                continue
            match_count = 0
            matched_words = []
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower):
                    match_count += 1
                    matched_words.append(keyword)
            if match_count > 0:
                matches[incident] = {
                    'count': match_count,
                    'words': matched_words,
                    'confidence': min(match_count * 20, 95)
                }
        
        if matches:
            best = max(matches.items(), key=lambda x: x[1]['count'])
            return {
                'suggested_incident': best[0],
                'confidence': best[1]['confidence'],
                'matched_keywords': best[1]['words'],
                'all_matches': matches
            }
        
        return {
            'suggested_incident': 'Other',
            'confidence': 50,
            'matched_keywords': [],
            'all_matches': {}
        }