def display_similarity_scores(docs_with_scores, threshold=0.0):
    """
    Display similarity scores in a formatted way
    """
    print("=" * 60)
    print("SIMILARITY SCORES REPORT")
    print("=" * 60)
    
    for i, (doc, distance_score) in enumerate(docs_with_scores):
        cosine_similarity = 1 - distance_score
        
        # Color coding based on similarity
        if cosine_similarity >= 0.8:
            status = "🟢 EXCELLENT"
        elif cosine_similarity >= 0.6:
            status = "🟡 GOOD"
        elif cosine_similarity >= 0.4:
            status = "🟠 MODERATE"
        else:
            status = "🔴 LOW"
        
        print(f"\nDoc {i+1}: {status}")
        print(f"  📊 Cosine Similarity: {cosine_similarity:.4f}")
        print(f"  📏 Distance Score: {distance_score:.4f}")
        print(f"  📄 Title: {doc.metadata.get('title', 'N/A')}")
        print(f"  📝 Preview: {doc.page_content[:100]}...")
        
        if cosine_similarity < threshold:
            print(f"  ⚠️  Below threshold ({threshold})")
    
    print("=" * 60)
    
    return [(doc, 1-score) for doc, score in docs_with_scores if (1-score) >= threshold]

def get_best_match_with_confidence(docs_with_scores):
    """
    Get the best match with confidence level
    """
    if not docs_with_scores:
        return None, "No matches found"
    
    best_doc, best_distance = docs_with_scores[0]
    best_similarity = 1 - best_distance
    
    if best_similarity >= 0.9:
        confidence = "Very High"
    elif best_similarity >= 0.7:
        confidence = "High"
    elif best_similarity >= 0.5:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return best_doc, f"Confidence: {confidence} (Score: {best_similarity:.4f})"