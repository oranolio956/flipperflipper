// Onboarding v3.11.0 - First-Time User Experience
class Onboarding {
  constructor() {
    this.currentStep = 0;
    this.steps = [
      {
        id: 'welcome',
        title: 'Welcome to PC Arbitrage Pro',
        content: this.renderWelcome.bind(this)
      },
      {
        id: 'settings',
        title: 'Configure Your Preferences',
        content: this.renderSettings.bind(this)
      },
      {
        id: 'complete',
        title: 'You\'re All Set!',
        content: this.renderComplete.bind(this)
      }
    ];
  }
  
  async start() {
    const { onboardingCompleted } = await chrome.storage.local.get('onboardingCompleted');
    if (onboardingCompleted) {
      console.log('[Onboarding] Already completed');
      return;
    }
    
    chrome.tabs.create({
      url: chrome.runtime.getURL('onboarding.html')
    });
  }
  
  init(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error('[Onboarding] Container not found');
      return;
    }
    
    this.render();
  }
  
  render() {
    const step = this.steps[this.currentStep];
    
    this.container.innerHTML = `
      <div style="max-width: 600px; margin: 50px auto; padding: 40px; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        <h1 style="text-align: center; margin-bottom: 30px;">${step.title}</h1>
        <div style="margin-bottom: 40px;">
          ${step.content()}
        </div>
        <div style="display: flex; justify-content: space-between;">
          ${this.currentStep > 0 ? `
            <button onclick="window.onboarding.previousStep()" style="padding: 12px 24px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer;">
              Back
            </button>
          ` : '<div></div>'}
          <button onclick="window.onboarding.nextStep()" style="padding: 12px 32px; background: #1976d2; color: white; border: none; border-radius: 8px; cursor: pointer;">
            ${this.currentStep < this.steps.length - 1 ? 'Continue' : 'Get Started'}
          </button>
        </div>
      </div>
    `;
  }
  
  renderWelcome() {
    return `
      <div style="text-align: center;">
        <p style="font-size: 18px; line-height: 1.6; color: #666;">
          Turn your marketplace expertise into profit with intelligent PC arbitrage tools.
        </p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 40px;">
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">🔍 Smart Scanning</h3>
            <p style="margin: 0; color: #666;">Automatically find profitable deals</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">💰 Profit Analysis</h3>
            <p style="margin: 0; color: #666;">Calculate ROI instantly</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">📊 Deal Pipeline</h3>
            <p style="margin: 0; color: #666;">Track deals from find to sold</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">🚀 Automation</h3>
            <p style="margin: 0; color: #666;">Save hours with smart tools</p>
          </div>
        </div>
      </div>
    `;
  }
  
  renderSettings() {
    return `
      <div>
        <p style="color: #666; margin-bottom: 30px;">Let's configure some basic settings to get you started.</p>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Your Budget Range</label>
          <div style="display: flex; gap: 10px; align-items: center;">
            <input type="number" id="minBudget" placeholder="Min" value="200" style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <span>to</span>
            <input type="number" id="maxBudget" placeholder="Max" value="1000" style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
          </div>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Minimum ROI Target</label>
          <select id="targetROI" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="20">20% or more</option>
            <option value="30" selected>30% or more</option>
            <option value="50">50% or more</option>
          </select>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Preferred Platforms</label>
          <div style="display: flex; gap: 15px;">
            <label style="display: flex; align-items: center; gap: 5px;">
              <input type="checkbox" value="facebook" checked> Facebook Marketplace
            </label>
            <label style="display: flex; align-items: center; gap: 5px;">
              <input type="checkbox" value="craigslist" checked> Craigslist
            </label>
          </div>
        </div>
      </div>
    `;
  }
  
  renderComplete() {
    return `
      <div style="text-align: center;">
        <div style="font-size: 48px; margin-bottom: 20px;">🎉</div>
        <p style="font-size: 18px; color: #666; margin-bottom: 30px;">
          You're all set! Your dashboard is ready to help you find profitable PC deals.
        </p>
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: left;">
          <h3 style="margin: 0 0 15px 0;">Quick Tips:</h3>
          <ul style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 8px;">Visit any marketplace and click our extension icon to scan deals</li>
            <li style="margin-bottom: 8px;">Star promising deals to track them in your pipeline</li>
            <li style="margin-bottom: 8px;">Check the dashboard daily for new opportunities</li>
          </ul>
        </div>
      </div>
    `;
  }
  
  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.saveStepData();
      this.currentStep++;
      this.render();
    } else {
      this.complete();
    }
  }
  
  previousStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.render();
    }
  }
  
  saveStepData() {
    // Save settings from step 2
    if (this.currentStep === 1) {
      const settings = {
        budget: {
          min: parseInt(document.getElementById('minBudget')?.value) || 200,
          max: parseInt(document.getElementById('maxBudget')?.value) || 1000
        },
        targetROI: parseInt(document.getElementById('targetROI')?.value) || 30
      };
      
      // Save to storage
      chrome.storage.local.set({ onboardingSettings: settings });
    }
  }
  
  async complete() {
    await chrome.storage.local.set({ onboardingCompleted: true });
    
    // Open dashboard
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html')
    });
    
    // Close onboarding tab
    window.close();
  }
}

// Create singleton instance
window.onboarding = new Onboarding();
