import json
import csv
from services.vectorstore import initialize_vector_store


def export_all_chromadb_data():
    """Xuất toàn bộ dữ liệu từ ChromaDB"""
    print("Đang lấy dữ liệu từ ChromaDB...")
    
    # Khởi tạo vectorstore trước
    vectorstore = initialize_vector_store()
    collection = vectorstore._collection
    
    # Lấy TOÀN BỘ dữ liệu (bỏ "ids" khỏi include)
    results = collection.get(
        include=["documents", "metadatas", "embeddings"]
    )
    
    # Lấy IDs riêng
    ids_results = collection.get()
    ids = ids_results["ids"] if "ids" in ids_results else []
    
    total_docs = len(results["documents"]) if results["documents"] else 0
    print(f"Tổng số documents: {total_docs}")
    
    # 1. Xuất ra JSON (đầy đủ nhất)
    full_data = {
        "total_documents": total_docs,
        "collection_name": collection.name,
        "documents": results["documents"],
        "metadatas": results["metadatas"],
        "ids": ids,
        "embeddings": results["embeddings"].tolist() if results["embeddings"] is not None else None
    }
    
    with open("chromadb_full_export.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã xuất toàn bộ dữ liệu ra: chromadb_full_export.json")
    
    # 2. Xuất ra CSV (dễ đọc)
    if results["documents"]:
        with open("chromadb_documents.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Document", "Title", "Image_URL", "Other_Metadata"])
            
            for i, doc in enumerate(results["documents"]):
                doc_id = ids[i] if i < len(ids) else ""
                metadata = results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
                
                title = metadata.get("title", "") if metadata else ""
                image_url = metadata.get("image_url", "") if metadata else ""
                other_meta = str({k: v for k, v in metadata.items() if k not in ["title", "image_url"]}) if metadata else ""
                
                writer.writerow([doc_id, doc, title, image_url, other_meta])
        
        print("✅ Đã xuất documents ra: chromadb_documents.csv")
    
    # 3. Xuất metadata riêng
    if results["metadatas"]:
        with open("chromadb_metadata.json", "w", encoding="utf-8") as f:
            json.dump(results["metadatas"], f, ensure_ascii=False, indent=2)
        print("✅ Đã xuất metadata ra: chromadb_metadata.json")
    
    # 4. Xuất chỉ documents và metadata (không có embeddings)
    documents_only = []
    for i, doc in enumerate(results["documents"] or []):
        documents_only.append({
            "id": ids[i] if i < len(ids) else f"doc_{i}",
            "document": doc,
            "metadata": results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
        })
    
    with open("chromadb_documents_only.json", "w", encoding="utf-8") as f:
        json.dump(documents_only, f, ensure_ascii=False, indent=2)
    print("✅ Đã xuất documents (không có embeddings) ra: chromadb_documents_only.json")
    
    # 5. In thống kê
    print(f"\n📊 THỐNG KÊ:")
    print(f"- Tổng documents: {total_docs}")
    print(f"- Tổng IDs: {len(ids)}")
    print(f"- Tổng metadata: {len(results['metadatas']) if results['metadatas'] else 0}")
    print(f"- Embeddings shape: {results['embeddings'].shape if results['embeddings'] is not None else 'None'}")
    
    # 6. Hiển thị sample
    print(f"\n📋 SAMPLE DATA (3 documents đầu):")
    for i in range(min(3, total_docs)):
        print(f"\n--- Document {i+1} ---")
        print(f"ID: {ids[i] if i < len(ids) else 'N/A'}")
        print(f"Content: {results['documents'][i][:200]}...")
        if results['metadatas'] and i < len(results['metadatas']):
            print(f"Metadata: {results['metadatas'][i]}")
    
    print(f"\n🎉 HOÀN THÀNH! Đã tạo 4 files:")
    print(f"1. chromadb_full_export.json - Toàn bộ dữ liệu")
    print(f"2. chromadb_documents.csv - CSV dễ đọc")
    print(f"3. chromadb_metadata.json - Chỉ metadata")
    print(f"4. chromadb_documents_only.json - Documents không có embeddings")


if __name__ == "__main__":
    export_all_chromadb_data()
