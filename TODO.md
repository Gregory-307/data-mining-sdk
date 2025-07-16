# Web-Search SDK - TODO List

## 🎯 **Phase 1: Create New Core Functions**

### **1.1 Enhanced DuckDuckGo Search Function**
- [ ] Create `duckduckgo_search_enhanced()` function
- [ ] Return structured results with titles, snippets, URLs
- [ ] Extract source information from URLs
- [ ] Test with various search terms

**Expected Return Format:**
```python
{
    "links": ["url1", "url2"],
    "tokens": ["bitcoin", "crypto"],
    "results": [
        {
            "title": "Bitcoin hits new high above $120,000...",
            "snippet": "Bitcoin traded above $120,000 to set a new record...",
            "url": "https://www.cnbc.com/2025/07/14/...",
            "source": "CNBC"
        }
    ]
}
```

### **1.2 General Article Extractor**
- [ ] Create `extract_article_content()` function
- [ ] Support any URL (not just Bloomberg/CNBC)
- [ ] Clean HTML extraction
- [ ] Extract metadata (title, author, date, source)
- [ ] Test on CNBC article: https://www.cnbc.com/2025/07/14/bitcoin-hits-new-all-time-high-above-120000-fueled-by-etf-inflows-crypto.html

**Expected Return Format:**
```python
{
    "title": "Bitcoin hits new high above $120,000...",
    "content": "The largest cryptocurrency by market capitalization...",
    "summary": "Bitcoin traded above $120,000...",
    "publish_date": "2025-07-14",
    "author": "Dylan Butts",
    "source": "CNBC"
}
```

## 🧹 **Phase 2: Improve Text Extraction**

### **2.1 Smart Content Extraction**
- [ ] Remove navigation/menu HTML
- [ ] Extract main article content
- [ ] Clean up formatting (remove extra spaces, line breaks)
- [ ] Extract metadata (title, author, date, source)
- [ ] Handle different site structures (CNBC, Bloomberg, Reuters, etc.)

### **2.2 Test Article Extraction**
- [ ] Test on CNBC article (provided link)
- [ ] Test on Bloomberg articles
- [ ] Test on Reuters articles
- [ ] Verify clean text output (no HTML garbage)

## 🔄 **Phase 3: Rename & Reorganize**

### **3.1 Rename Current Functions**
- [ ] Rename current `search_and_parse()` to `search_and_parse_basic()`
- [ ] Create new enhanced `search_and_parse()` as default
- [ ] Update all imports and references
- [ ] Maintain backward compatibility

### **3.2 Update Function Categories**
- [ ] Update documentation categories
- [ ] Add "Enhanced Search" section
- [ ] Add "Article Extraction" section
- [ ] Keep "Basic Search" as legacy option

## 📁 **Phase 4: Implementation Steps**

### **4.1 Create New Files**
- [ ] `web_search_sdk/scrapers/duckduckgo_enhanced.py` - Enhanced DuckDuckGo parser
- [ ] `web_search_sdk/scrapers/article_extractor.py` - General article extraction
- [ ] `web_search_sdk/utils/content_cleaner.py` - HTML cleaning utilities

### **4.2 Update Existing Files**
- [ ] `web_search_sdk/scrapers/search.py` - Add enhanced version
- [ ] `web_search_sdk/scrapers/paywall.py` - Deprecate, redirect to article_extractor
- [ ] `docs/demo_notebook_v2_draft.py` - Update examples
- [ ] Update `__init__.py` files with new exports

### **4.3 Testing**
- [ ] Test on CNBC article - Verify clean extraction
- [ ] Test on multiple sites - Bloomberg, Reuters, etc.
- [ ] Update smoke test - Include new functions
- [ ] Add unit tests for new functions

## 📚 **Phase 5: Documentation Updates**

### **5.1 Update Cheatsheet**
- [ ] Add new function examples to `docs/CHEATSHEET.md`
- [ ] Show structured output format
- [ ] Include article extraction examples
- [ ] Update API reference table

### **5.2 Update Notebook**
- [ ] Add new demo cells to `docs/demo_notebook_v2_draft.py`
- [ ] Show before/after text extraction
- [ ] Demonstrate sentiment analysis use case
- [ ] Update menu/navigation links

## 🚀 **Immediate Next Steps (Priority Order)**

1. **Create `extract_article_content()` function** and test on CNBC link
2. **Enhance DuckDuckGo parser** to return structured results
3. **Update `search_and_parse()`** to use enhanced version by default
4. **Keep legacy function** as `search_and_parse_basic()` for backward compatibility

## 🔧 **Technical Requirements**

### **Content Extraction Requirements**
- Clean HTML removal
- Preserve article structure
- Extract meaningful metadata
- Handle different site layouts
- Robust error handling

### **Backward Compatibility**
- Keep existing function names working
- Add deprecation warnings for old functions
- Maintain same return formats for existing functions
- Update documentation to guide users to new functions

### **Testing Requirements**
- Test on real articles (CNBC, Bloomberg, Reuters)
- Verify clean text output
- Test error handling for invalid URLs
- Performance testing for large articles

---

**Last Updated**: 2025-01-27
**Priority**: High - Core functionality improvement
**Estimated Effort**: 2-3 days 