"""
Provar AI Test Case Generator - Streamlit App
Complete AI-powered test automation for Salesforce with Vision AI
"""

import streamlit as st
import base64
import json
import requests
from datetime import datetime
from io import BytesIO
from PIL import Image

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Provar AI Test Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .element-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .code-display {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1.5rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'generated_test' not in st.session_state:
    st.session_state.generated_test = None

if 'detected_elements' not in st.session_state:
    st.session_state.detected_elements = []

if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

if 'screenshots' not in st.session_state:
    st.session_state.screenshots = []

# ============================================================================
# AI FUNCTIONS
# ============================================================================

def analyze_screenshot_with_ai(image_data):
    """Analyze screenshot using Claude Vision API"""
    try:
        API_URL = 'https://api.anthropic.com/v1/messages'
        
        response = requests.post(
            API_URL,
            headers={'Content-Type': 'application/json'},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this Salesforce UI screenshot and identify all interactive elements.

Return ONLY a JSON array with this exact format (no other text):
[
  {
    "type": "input|button|dropdown|link|checkbox|textarea",
    "label": "visible text or placeholder",
    "id": "suggested element ID or name",
    "xpath": "suggested xpath locator",
    "action": "click|enterText|select|check"
  }
]

Focus on:
- Input fields (text, email, password)
- Buttons (submit, cancel, save, etc.)
- Dropdowns/select boxes
- Checkboxes and radio buttons
- Links and navigation elements"""
                        }
                    ]
                }]
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['content'][0]['text']
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                elements = json.loads(json_match.group(0))
                return elements
        
        return []
    except Exception as e:
        st.error(f"Screenshot analysis failed: {str(e)}")
        return []

def generate_provar_test(test_name, url, description, dom_html, detected_elements):
    """Generate Provar test case using Claude AI"""
    try:
        API_URL = 'https://api.anthropic.com/v1/messages'
        
        # Build comprehensive prompt
        elements_info = ""
        if detected_elements:
            elements_info = f"\n**Detected UI Elements from Screenshots:**\n{json.dumps(detected_elements, indent=2)}\n"
        
        dom_info = ""
        if dom_html:
            dom_info = f"\n**Page DOM/HTML:**\n{dom_html}\n"
        
        prompt = f"""You are a Provar test automation expert for Salesforce. Generate a complete, production-ready Provar test case in XML format.

**Test Details:**
- Test Name: {test_name}
- URL: {url or 'Salesforce Login Page'}
- Description: {description}

{elements_info}
{dom_info}

**CRITICAL REQUIREMENTS:**

1. **Use ONLY Salesforce-specific Provar actions:**
   - SfLogin (for login)
   - SfNavigate (for navigation)
   - SfClick (for clicking elements)
   - SfEnterText (for entering text)
   - SfSelect (for dropdowns)
   - SfVerify (for assertions)
   - SfWait (for waiting)

2. **Locator Strategy (in order of preference):**
   - Id (most reliable)
   - Name
   - XPath (for complex elements)
   - CSS Selector (as fallback)

3. **Include proper structure:**
   - Test case ID (use test_name without spaces)
   - Summary
   - Description
   - Steps with sequential IDs
   - Proper XML formatting

4. **Best Practices:**
   - Add SfWait after page navigation
   - Use explicit waits before interactions
   - Include assertions after critical actions
   - Add error handling steps
   - Use descriptive step names

**Required XML Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<testCase id="TestCaseId">
  <summary>Brief summary</summary>
  <description>Detailed description</description>
  <steps>
    <step id="1" action="SfNavigate">
      <url>URL_HERE</url>
      <waitForPageLoad>true</waitForPageLoad>
    </step>
    <step id="2" action="SfWait">
      <timeout>5000</timeout>
    </step>
    <step id="3" action="SfClick">
      <locator type="Id">elementId</locator>
      <description>Click element description</description>
    </step>
    <step id="4" action="SfEnterText">
      <locator type="Id">inputFieldId</locator>
      <text>value_to_enter</text>
      <description>Enter text description</description>
    </step>
    <step id="5" action="SfVerify">
      <locator type="XPath">//div[contains(text(),'Success')]</locator>
      <expected>visible</expected>
      <description>Verify success message</description>
    </step>
  </steps>
  <metadata>
    <generatedBy>Provar AI Generator</generatedBy>
    <timestamp>{datetime.now().isoformat()}</timestamp>
    <version>1.0</version>
  </metadata>
</testCase>
```

**Generate the complete Provar XML test case now. Return ONLY the XML code, no explanations or markdown.**"""

        response = requests.post(
            API_URL,
            headers={'Content-Type': 'application/json'},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            xml_content = data['content'][0]['text']
            
            # Extract XML from markdown code blocks if present
            import re
            xml_match = re.search(r'```xml\n([\s\S]*?)\n```', xml_content)
            if xml_match:
                xml_content = xml_match.group(1)
            else:
                xml_match = re.search(r'```\n([\s\S]*?)\n```', xml_content)
                if xml_match:
                    xml_content = xml_match.group(1)
            
            return xml_content.strip()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Test generation failed: {str(e)}")
        return None

def validate_provar_test(xml_content):
    """Validate generated Provar test case"""
    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    # Check XML structure
    if not xml_content.startswith('<?xml'):
        validation['warnings'].append("Missing XML declaration")
    
    # Required elements
    if '<testCase' not in xml_content:
        validation['errors'].append("Missing <testCase> root element")
        validation['is_valid'] = False
    
    if '<summary>' not in xml_content:
        validation['warnings'].append("Missing <summary> element")
    
    if '<steps>' not in xml_content:
        validation['errors'].append("Missing <steps> element")
        validation['is_valid'] = False
    
    # Salesforce-specific actions
    sf_actions = ['SfNavigate', 'SfClick', 'SfEnterText', 'SfVerify', 'SfLogin', 'SfWait', 'SfSelect']
    has_sf_actions = any(action in xml_content for action in sf_actions)
    
    if not has_sf_actions:
        validation['warnings'].append("No Salesforce-specific actions found. Generic actions may not work in Provar.")
    else:
        validation['info'].append("✓ Contains Salesforce-specific Provar actions")
    
    # Check for locators
    if '<locator' not in xml_content:
        validation['warnings'].append("No element locators found")
    else:
        validation['info'].append("✓ Contains element locators")
    
    # Count steps
    import re
    step_matches = re.findall(r'<step', xml_content)
    if step_matches:
        validation['info'].append(f"✓ Contains {len(step_matches)} test steps")
    
    # Check for waits
    if 'SfWait' in xml_content or 'waitForPageLoad' in xml_content:
        validation['info'].append("✓ Includes wait conditions")
    
    # Check for assertions
    if 'SfVerify' in xml_content or 'Assert' in xml_content:
        validation['info'].append("✓ Includes verification/assertions")
    
    return validation

# ============================================================================
# MAIN APP
# ============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>⚡ Provar AI Test Generator</h1>
    <p style="font-size: 1.2rem; margin-top: 0.5rem;">Salesforce Test Automation with Vision AI</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.markdown("---")
    
    st.markdown("### 📊 Session Stats")
    if st.session_state.generated_test:
        st.success("✅ Test Generated")
    else:
        st.info("⏳ No test generated yet")
    
    st.metric("Screenshots Uploaded", len(st.session_state.screenshots))
    st.metric("Elements Detected", len(st.session_state.detected_elements))
    
    st.markdown("---")
    
    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    - Upload clear screenshots of your Salesforce UI
    - Be specific in test descriptions
    - Include field names and expected outcomes
    - Use Salesforce field API names when known
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.generated_test = None
        st.session_state.detected_elements = []
        st.session_state.validation_results = None
        st.session_state.screenshots = []
        st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📝 Input & Generate", "🤖 AI Analysis", "📄 Generated Test"])

# ============================================================================
# TAB 1: INPUT & GENERATE
# ============================================================================

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📋 Test Details")
        
        test_name = st.text_input(
            "Test Case Name *",
            placeholder="e.g., SF_Account_Creation_Test",
            help="Use underscores instead of spaces"
        )
        
        url = st.text_input(
            "Salesforce URL",
            placeholder="https://login.salesforce.com or your instance URL",
            help="Optional - will use login.salesforce.com if not provided"
        )
        
        st.markdown("### 📝 Test Scenario (Natural Language) *")
        description = st.text_area(
            "Describe what you want to test",
            placeholder="""Example:
1. Login to Salesforce with valid credentials
2. Navigate to Accounts tab
3. Click 'New' button
4. Fill in Account Name as 'Test Account'
5. Select Type as 'Customer - Direct'
6. Click Save button
7. Verify account is created successfully
8. Verify success message 'Account created' appears""",
            height=300,
            help="Be specific about actions, field names, and expected results"
        )
    
    with col2:
        st.markdown("### 📸 Screenshots (Optional)")
        st.info("Upload screenshots for AI to detect fields and buttons automatically")
        
        uploaded_files = st.file_uploader(
            "Upload Salesforce UI screenshots",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="AI will analyze screenshots to detect UI elements"
        )
        
        if uploaded_files:
            st.session_state.screenshots = []
            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)
                st.session_state.screenshots.append({
                    'name': uploaded_file.name,
                    'image': image,
                    'data': base64.b64encode(uploaded_file.getvalue()).decode()
                })
            
            st.success(f"✅ {len(uploaded_files)} screenshot(s) uploaded")
            
            # Show thumbnails
            cols = st.columns(min(len(uploaded_files), 3))
            for idx, img_data in enumerate(st.session_state.screenshots):
                with cols[idx % 3]:
                    st.image(img_data['image'], caption=img_data['name'], use_container_width=True)
        
        st.markdown("### 🌐 DOM/HTML (Optional)")
        dom_html = st.text_area(
            "Paste page HTML/DOM structure",
            placeholder="""<div class="slds-form">
  <input id="username" name="username" />
  <input id="password" type="password" />
  <button class="slds-button">Login</button>
</div>""",
            height=200,
            help="Paste Salesforce page HTML for better element detection"
        )
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚡ Generate Provar Test Case", use_container_width=True, type="primary"):
            if not test_name or not description:
                st.error("❌ Please provide Test Name and Description")
            else:
                with st.spinner("🤖 AI is analyzing and generating your test case..."):
                    # Analyze screenshots first if available
                    if st.session_state.screenshots and not st.session_state.detected_elements:
                        st.info("🔍 Analyzing screenshots with Vision AI...")
                        for img_data in st.session_state.screenshots:
                            elements = analyze_screenshot_with_ai(img_data['data'])
                            if elements:
                                st.session_state.detected_elements.extend(elements)
                    
                    # Generate test
                    st.info("✍️ Generating Provar test case...")
                    generated_xml = generate_provar_test(
                        test_name=test_name,
                        url=url,
                        description=description,
                        dom_html=dom_html,
                        detected_elements=st.session_state.detected_elements
                    )
                    
                    if generated_xml:
                        st.session_state.generated_test = generated_xml
                        
                        # Validate
                        st.info("✅ Validating test case...")
                        st.session_state.validation_results = validate_provar_test(generated_xml)
                        
                        st.success("🎉 Test case generated successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to generate test case. Please try again.")

# ============================================================================
# TAB 2: AI ANALYSIS
# ============================================================================

with tab2:
    st.markdown("### 🤖 AI-Detected Elements from Screenshots")
    
    if st.session_state.detected_elements:
        st.success(f"✅ Found {len(st.session_state.detected_elements)} UI elements")
        
        for idx, element in enumerate(st.session_state.detected_elements, 1):
            with st.container():
                st.markdown(f"""
                <div class="element-card">
                    <strong>Element {idx}: {element.get('label', 'Unknown')}</strong><br>
                    <small>
                    Type: <code>{element.get('type', 'N/A')}</code> | 
                    Action: <code>{element.get('action', 'N/A')}</code><br>
                    ID: <code>{element.get('id', 'N/A')}</code><br>
                    XPath: <code>{element.get('xpath', 'N/A')}</code>
                    </small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📸 Upload screenshots in the 'Input & Generate' tab to detect UI elements automatically")
        
        st.markdown("""
        ### How Vision AI Works:
        
        1. **Upload Screenshots** - Capture your Salesforce UI
        2. **AI Analysis** - Claude Vision identifies all interactive elements
        3. **Element Detection** - Buttons, inputs, dropdowns, links, etc.
        4. **Locator Generation** - Suggests IDs, XPaths, and CSS selectors
        5. **Test Integration** - Uses detected elements in generated test
        
        This helps create more accurate and reliable test cases!
        """)

# ============================================================================
# TAB 3: GENERATED TEST
# ============================================================================

with tab3:
    if st.session_state.generated_test:
        # Validation Results
        if st.session_state.validation_results:
            validation = st.session_state.validation_results
            
            if validation['is_valid']:
                st.markdown("""
                <div class="success-box">
                    <h3>✅ Validation Passed</h3>
                    <p>Test case is valid and ready to import into Provar!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="error-box">
                    <h3>⚠️ Validation Issues Found</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Show validation details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if validation['errors']:
                    st.markdown("**❌ Errors:**")
                    for error in validation['errors']:
                        st.error(error)
            
            with col2:
                if validation['warnings']:
                    st.markdown("**⚠️ Warnings:**")
                    for warning in validation['warnings']:
                        st.warning(warning)
            
            with col3:
                if validation['info']:
                    st.markdown("**ℹ️ Info:**")
                    for info in validation['info']:
                        st.info(info)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.generated_test, language='xml')
                st.success("✅ Code displayed above - select and copy!")
        
        with col2:
            # Download button
            st.download_button(
                label="📥 Download .testcase",
                data=st.session_state.generated_test,
                file_name=f"{test_name.replace(' ', '_')}.testcase" if 'test_name' in locals() else "provar_test.testcase",
                mime="text/xml",
                use_container_width=True
            )
        
        with col3:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.generated_test = None
                st.session_state.validation_results = None
                st.rerun()
        
        st.markdown("---")
        
        # Display XML
        st.markdown("### 📄 Generated Provar Test Case (XML)")
        st.code(st.session_state.generated_test, language='xml')
        
        st.markdown("---")
        
        # Import instructions
        st.markdown("""
        ### 📥 How to Import into Provar
        
        1. **Download** the .testcase file using the button above
        2. **Open** your Provar project in Eclipse or VS Code
        3. **Right-click** on your `tests` folder
        4. **Select** Import → Provar Test Case
        5. **Browse** and select the downloaded .testcase file
        6. **Click** Import
        7. **Review** the test steps and adjust if needed
        8. **Run** the test against your Salesforce org!
        
        ### 🎯 Next Steps
        
        - Review all locators (IDs, XPaths) and update if needed
        - Add your Salesforce credentials to test data
        - Configure connection settings in Provar
        - Run the test in debug mode first
        - Add to your test suite for automation
        """)
    else:
        st.info("📝 Generate a test case in the 'Input & Generate' tab first")
        
        st.markdown("""
        ### What You'll Get:
        
        ✅ **Production-ready Provar test case in XML format**
        - Salesforce-specific actions (SfLogin, SfNavigate, SfClick, etc.)
        - Proper element locators (Id, Name, XPath)
        - Wait conditions and error handling
        - Assertions and verifications
        - Complete metadata
        
        ✅ **AI-powered accuracy**
        - Vision AI detects UI elements from screenshots
        - Analyzes DOM structure for better locators
        - Generates based on natural language description
        - Validates test case structure
        
        ✅ **Ready to import**
        - Download as .testcase file
        - Direct import into Provar
        - No manual coding required
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p style='font-size: 1.1rem;'><strong>⚡ Provar AI Test Generator</strong></p>
    <p>Powered by Claude AI Vision | Generate Salesforce test cases in seconds</p>
    <p style='font-size: 0.9rem; color: #999;'>Natural Language → Screenshots → Provar Test Case</p>
</div>
""", unsafe_allow_html=True)
