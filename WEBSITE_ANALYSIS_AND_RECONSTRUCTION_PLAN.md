# CupidBot.ai - Website Analysis & 1:1 Reconstruction Plan

## Executive Summary
This document provides a complete analysis of the CupidBot.ai website and a detailed plan for creating an exact 1:1 replica. All assets have been downloaded and analyzed.

---

## 1. Website Structure Analysis

### Pages Discovered & Downloaded:
1. **Home Page** (`index.html`)
   - Main landing page with hero section
   - Features section with accordion
   - Product showcase
   - Newsletter signup
   - Press mentions (Vice, NY Post, Yahoo, Futurism, Fox, BFMTV)

2. **Contact Page** (`contact.html`)
   - Contact form
   - Company information

3. **Product Page** (`product/beta.html` / `product/bot`)
   - Product details
   - Pricing information ($30 USD, originally $90 USD)
   - Product images and description
   - Purchase functionality (Stripe integration)

4. **Policies Page** (`post/policies.html`)
   - Terms and conditions
   - User policies

5. **Privacy Policy Page** (`post/privacy-policy.html`)
   - Privacy information
   - Data handling policies

### Navigation Structure:
```
Home
├── Home (index.html)
├── Contact (contact.html)
├── OFM (External: https://t.me/cupidbotg)
└── Get Dates (product/beta.html)

Footer Links
├── Pages
│   ├── Home
│   ├── Contact
│   └── Update subscription (External: Stripe billing)
└── Policies
    ├── Policies
    └── Privacy
```

---

## 2. Technology Stack

### Frontend Framework:
- **Webflow** (CMS and design platform)
  - Site ID: 6440ef10d027f97f198da940
  - Page ID: 64447a357588016951aff5e3
  - Built: Thu Nov 02 2023 21:36:36 GMT+0000

### CSS Framework:
- Custom Webflow CSS (cupidbotai.webflow.7be6c7fd7.min.css)
- Responsive design with breakpoints
- Custom cursor styling
- Smooth font rendering (antialiased)

### JavaScript Libraries:
1. **jQuery 3.5.1** (d3e54v103j8qbb.cloudfront.net)
2. **Google WebFont Loader 1.6.26**
3. **Webflow.js** (bb8104efa.js)
4. **Google Analytics** (gtag.js)
   - Property ID: G-9VBQ03HHF3
   - UA ID: UA-259289896-1

### Fonts:
- **Roboto Mono** (regular) - Google Fonts
- **Syne** (regular, 500) - Google Fonts

### External Services:
1. **Form Backend**: https://cupidbot-382905.uc.r.appspot.com/form
2. **Stripe Payments**: Integrated for product purchases
3. **Google Analytics**: Multiple tracking codes
4. **Social Media**:
   - Twitter: https://twitter.com/cupidbotai
   - Discord: https://discord.gg/JhZESyNhBy
   - Instagram: https://www.instagram.com/cupidbot.ai/
   - Telegram: https://t.me/cupidbotg

---

## 3. Assets Inventory

### CSS Files (1 file):
- `cupidbotai.webflow.min.css` - Main stylesheet (minified)

### JavaScript Files (3 files):
- `jquery-3.5.1.min.js` - jQuery library
- `webfont.js` - Google WebFont loader
- `webflow.js` - Webflow interactions and animations

### Images (19 files):

**Icons:**
- `favicon.png` - Browser favicon
- `apple-touch-icon.png` - iOS home screen icon

**Hero Images:**
- `hero-image.png` (983w) - Main hero image
- `hero-image-500.png` - Responsive variant
- `hero-image-800.png` - Responsive variant

**Social Media Icons:**
- `twitter.png` - Twitter icon
- `discord.png` - Discord icon
- `instagram.png` - Instagram icon

**Press Logos:**
- `vice.webp` + `vice-500.webp` - Vice logo
- `nypost.png` - NY Post logo
- `futurism.png` - Futurism logo
- `yahoo.png` - Yahoo logo
- `bfmtv.webp` - BFMTV logo
- `fox.png` - Fox logo

**Content Images:**
- `calendar.png` + `calendar-500.png` - Calendar illustration
- `product-screenshot.png` + `product-screenshot-500.png` - Product screenshots

---

## 4. Design Analysis

### Color Scheme:
The website uses a modern, minimalist color palette (extracted from visual inspection):
- Primary: Dark background with light text (dark mode style)
- Accent: Likely pink/red tones (CupidBot theme)
- Text: High contrast for readability

### Typography:
- **Headings**: Syne font (modern, geometric)
- **Body/Code**: Roboto Mono (monospace, tech feel)

### Layout:
- Responsive grid system
- Mobile-first design
- Hamburger menu for mobile
- Sticky navigation header
- Footer with sitemap and social links

### Key UI Components:
1. **Navigation Bar**
   - Logo (text-based: "CupidBot.ai")
   - Menu items (Home, Contact, OFM)
   - CTA button ("get dates")
   - Social media icons
   - Mobile menu toggle

2. **Hero Section**
   - Large headline: "AI that gets you dates"
   - Subheading with value proposition
   - CTA button
   - Hero image (illustration)

3. **Featured In Section**
   - Media logos in a horizontal scrolling/grid layout
   - "Featured in" meta text

4. **Values Section**
   - Three-column grid
   - Numbered badges (01, 02, 03)
   - "Fill up your calendar with dates" headline
   - Calendar image
   - Features:
     - Never swipe again
     - Never small talk again
     - Start actually dating

5. **Features/FAQ Section**
   - Accordion-style expandable items
   - SVG icons for expand/collapse
   - Features listed:
     - Get several dates a week
     - Get exactly what you're looking for
     - Only match with your ideal type
     - Choose your chatting tone
     - Automatic followups
     - Calendar integration
     - Don't match with people you know
     - Safe to use
     - All major languages supported

6. **Product Section**
   - Product card with image
   - Pricing (compare at price + sale price)
   - Product name and link

7. **Newsletter Section**
   - Email signup form
   - "Stay updated" heading
   - Form submission to Google App Engine

8. **Footer**
   - Company description
   - Social media links
   - Page navigation
   - Policies links
   - Copyright notice

---

## 5. Interactive Features

### JavaScript Functionality:
1. **Mobile Menu Toggle**
   - Three-line hamburger icon
   - Slide-in/out animation

2. **Accordion Component**
   - Expandable FAQ items
   - Smooth transitions
   - Plus/minus icon toggle

3. **Form Handling**
   - Email validation
   - Custom form submission (overrides default Webflow)
   - Success/error messages
   - POST to: https://cupidbot-382905.uc.r.appspot.com/form

4. **Analytics Tracking**
   - Automatic link click tracking
   - Custom event tracking for buttons (class: "ga-event")
   - E-commerce tracking for product views

5. **Link Prefetching**
   - Prefetch hints for product pages (performance optimization)

6. **Cursor Effects**
   - Custom cursor wrapper (likely for hover effects)
   - "View" cursor text element

---

## 6. External Dependencies & CDN Resources

### Fonts (Google Fonts):
```
https://fonts.googleapis.com
https://fonts.gstatic.com
- Roboto Mono:regular
- Syne:regular,500
```

### CDN Resources:
1. **Webflow CDN**:
   - CSS: https://cdn.prod.website-files.com/6440ef10d027f97f198da940/css/
   - JS: https://cdn.prod.website-files.com/6440ef10d027f97f198da940/js/
   - Images: https://cdn.prod.website-files.com/6440ef10d027f97f198da940/
   - Product images: https://cdn.prod.website-files.com/6440ef10d027f956128da952/

2. **CloudFront CDN**:
   - jQuery: https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.js

3. **Google CDN**:
   - WebFont: https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js
   - Analytics: https://www.googletagmanager.com/gtag/js

### API Endpoints:
- Form submission: https://cupidbot-382905.uc.r.appspot.com/form
- Stripe billing: https://billing.stripe.com/p/login/6oE4kjggub4u0yAcMM

---

## 7. File Structure (Current Download)

```
/workspace/cupidbot-website-backup/
└── cupidbot.ai/
    ├── index.html
    ├── contact.html
    ├── product/
    │   └── beta.html
    ├── post/
    │   ├── policies.html
    │   └── privacy-policy.html
    └── assets/
        ├── css/
        │   └── cupidbotai.webflow.min.css
        ├── js/
        │   ├── jquery-3.5.1.min.js
        │   ├── webfont.js
        │   └── webflow.js
        ├── images/
        │   ├── favicon.png
        │   ├── apple-touch-icon.png
        │   ├── hero-image.png
        │   ├── hero-image-500.png
        │   ├── hero-image-800.png
        │   ├── twitter.png
        │   ├── discord.png
        │   ├── instagram.png
        │   ├── vice.webp
        │   ├── vice-500.webp
        │   ├── nypost.png
        │   ├── futurism.png
        │   ├── yahoo.png
        │   ├── bfmtv.webp
        │   ├── fox.png
        │   ├── calendar.png
        │   ├── calendar-500.png
        │   ├── product-screenshot.png
        │   └── product-screenshot-500.png
        └── fonts/
            (fonts loaded from Google Fonts CDN)
```

---

## 8. Step-by-Step Reconstruction Plan

### Phase 1: Setup & Organization ✓ (COMPLETED)
- [x] Download all HTML pages
- [x] Download all CSS files
- [x] Download all JavaScript files
- [x] Download all images and icons
- [x] Create organized folder structure

### Phase 2: Localize External Resources (NEXT)
- [ ] Update all HTML files to reference local assets instead of CDN
- [ ] Update CSS file paths in HTML (CDN → local)
- [ ] Update JavaScript file paths in HTML (CDN → local)
- [ ] Update image paths in HTML (CDN → local)
- [ ] Test that all resources load correctly

### Phase 3: Update Links & References
- [ ] Convert all absolute URLs to relative paths
- [ ] Update navigation links across all pages
- [ ] Ensure all internal links work correctly
- [ ] Update form action URLs (or keep external if needed)

### Phase 4: Font Integration
- [ ] Option A: Keep Google Fonts CDN (recommended for performance)
- [ ] Option B: Download fonts locally and update references
  - Download Roboto Mono (regular)
  - Download Syne (regular, 500)
  - Create local @font-face declarations

### Phase 5: External Services Configuration
- [ ] Decide on form backend:
  - Keep existing: https://cupidbot-382905.uc.r.appspot.com/form
  - Or replace with new backend (PHP, Node.js, etc.)
- [ ] Update Google Analytics tracking IDs (or remove for testing)
- [ ] Configure Stripe integration (keep or update)
- [ ] Update social media links if needed

### Phase 6: Testing & Validation
- [ ] Test all pages load correctly
- [ ] Test navigation between pages
- [ ] Test mobile responsive design
- [ ] Test forms and interactions
- [ ] Test accordion functionality
- [ ] Validate HTML/CSS
- [ ] Check cross-browser compatibility
- [ ] Test on multiple devices

### Phase 7: Optimization
- [ ] Optimize images (compress if needed)
- [ ] Minify CSS/JS if not already
- [ ] Add meta tags for SEO
- [ ] Test page load speed
- [ ] Add security headers
- [ ] Setup 301 redirects if needed

### Phase 8: Deployment
- [ ] Choose hosting platform (Netlify, Vercel, AWS S3, etc.)
- [ ] Configure domain/subdomain
- [ ] Setup SSL certificate
- [ ] Deploy website
- [ ] Test live site
- [ ] Setup monitoring/analytics

---

## 9. Detailed Action Items

### To Create Exact 1:1 Copy:

#### A. Update HTML Files (All 5 files)

**File: `index.html`**
Replace all CDN references:
```html
<!-- OLD -->
<link href="https://cdn.prod.website-files.com/.../css/cupidbotai.webflow.7be6c7fd7.min.css" rel="stylesheet"/>
<!-- NEW -->
<link href="assets/css/cupidbotai.webflow.min.css" rel="stylesheet"/>

<!-- OLD -->
<script src="https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js"></script>
<!-- NEW -->
<script src="assets/js/webfont.js"></script>

<!-- OLD -->
<script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js"></script>
<!-- NEW -->
<script src="assets/js/jquery-3.5.1.min.js"></script>

<!-- OLD -->
<script src="https://cdn.prod.website-files.com/.../js/webflow.bb8104efa.js"></script>
<!-- NEW -->
<script src="assets/js/webflow.js"></script>

<!-- OLD -->
<img src="https://cdn.prod.website-files.com/.../6440f4e50740bf677fa49018_bayle__heartbreaker_narrow.png" />
<!-- NEW -->
<img src="assets/images/hero-image.png" />
```

Repeat for all image references in:
- Hero section
- Press logos (vice, nypost, futurism, yahoo, bfmtv, fox)
- Social media icons (twitter, discord, instagram)
- Calendar image
- Product screenshots
- Favicons

**Apply same updates to:**
- `contact.html`
- `product/beta.html`
- `post/policies.html`
- `post/privacy-policy.html`

#### B. CSS Verification
- Open `assets/css/cupidbotai.webflow.min.css`
- Check for any external image/font references
- If found, download and localize those as well

#### C. JavaScript Verification
- Check `webflow.js` for hardcoded CDN paths
- Update any found references to local paths

#### D. Create Index/Documentation
- Create README.md with setup instructions
- Document any external services still in use
- Note any configuration needed

---

## 10. Tools & Technologies Needed

### Already Available:
- ✓ wget (for downloading)
- ✓ curl (for testing)
- ✓ Basic file system tools

### May Need:
- Text editor / IDE (VS Code, Sublime, etc.)
- Web browser with dev tools (Chrome, Firefox)
- Local web server for testing:
  - Python: `python -m http.server 8000`
  - Node.js: `npx http-server`
  - PHP: `php -S localhost:8000`

### For Development:
- Git (version control)
- Node.js/npm (if building custom backend)
- Image optimization tools (optional):
  - ImageOptim, TinyPNG, etc.

---

## 11. Known External Dependencies That Must Remain

These cannot be fully localized without breaking functionality:

1. **Google Fonts** (can localize, but CDN is recommended)
2. **Form Backend** (https://cupidbot-382905.uc.r.appspot.com/form)
   - Would need to create replacement or keep
3. **Google Analytics** (https://www.googletagmanager.com/gtag/js)
   - Can be removed or updated with new tracking ID
4. **Stripe Integration** (for payments)
   - Keep for e-commerce functionality
5. **Social Media Links** (external by nature)

---

## 12. Estimated Timeline

- **Phase 1**: Setup & Organization - ✓ COMPLETED
- **Phase 2**: Localize Resources - 1-2 hours
- **Phase 3**: Update Links - 1 hour
- **Phase 4**: Font Integration - 30 minutes
- **Phase 5**: External Services - 1-2 hours (depends on requirements)
- **Phase 6**: Testing - 2-3 hours
- **Phase 7**: Optimization - 1-2 hours
- **Phase 8**: Deployment - 1-2 hours

**Total Estimated Time**: 8-13 hours for complete 1:1 replica

---

## 13. Current Status

✅ **COMPLETED:**
- All 5 HTML pages downloaded
- All CSS files downloaded (1 file)
- All JavaScript files downloaded (3 files)
- All images downloaded (19 files)
- Organized folder structure created
- Complete website analysis documented

📋 **NEXT STEPS:**
1. Update HTML files to use local asset paths
2. Test locally to ensure all resources load
3. Configure any external services needed
4. Deploy to hosting platform

---

## 14. Important Notes

1. **Webflow Attribution**: The site was built with Webflow. The HTML contains Webflow-specific attributes (data-wf-*) which can remain.

2. **Forms**: The newsletter form submits to Google App Engine (https://cupidbot-382905.uc.r.appspot.com/form). You'll need to either:
   - Keep this endpoint (may not work if it's configured for specific domains)
   - Create a new form backend
   - Use a service like Formspree, Netlify Forms, etc.

3. **Analytics**: Contains two Google Analytics properties. Update or remove based on needs.

4. **E-commerce**: Product page has Stripe integration. May need to update Stripe keys/configuration.

5. **Images**: All images have been downloaded in their available sizes. Responsive images use srcset for different viewport sizes.

6. **Browser Compatibility**: Website uses modern CSS/JS. Should work in all modern browsers (Chrome, Firefox, Safari, Edge).

---

## 15. Recommendation

**For fastest deployment:**
1. Run the localization script (Phase 2) to update all paths
2. Test locally with a simple HTTP server
3. Deploy to Netlify or Vercel (both have free tiers)
4. Configure custom domain if needed

**This approach will have your exact replica live in under 2 hours.**

---

## Contact & Support

If you need help with any phase of the reconstruction, the assets are ready in:
```
/workspace/cupidbot-website-backup/
```

All files are organized and ready for the next steps.

---

**Document Created**: 2025-10-17
**Website Analyzed**: https://cupidbot.ai
**Status**: ✅ Analysis Complete - Ready for Reconstruction
