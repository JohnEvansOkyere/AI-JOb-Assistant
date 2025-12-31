/**
 * Landing Page
 * Public-facing homepage inspired by n8n design
 */

'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useEffect, useState, useRef } from 'react'
import { 
  Sparkles, 
  Users, 
  FileText, 
  Brain, 
  MessageSquare, 
  BarChart3, 
  Zap,
  CheckCircle2,
  ArrowRight,
  Play,
  Shield,
  Code2,
  Workflow,
  ChevronDown,
  Star,
  Lock,
  Globe,
  Award,
  CheckCircle,
  Mail,
  Calendar
} from 'lucide-react'
import Link from 'next/link'

// Animated Counter Component
function AnimatedCounter({ 
  target, 
  suffix = '', 
  prefix = '',
  duration = 2000 
}: { 
  target: number; 
  suffix?: string; 
  prefix?: string;
  duration?: number;
}) {
  const [count, setCount] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated) {
            setHasAnimated(true)
            const startTime = Date.now()
            const animate = () => {
              const elapsed = Date.now() - startTime
              const progress = Math.min(elapsed / duration, 1)
              const easeOutQuart = 1 - Math.pow(1 - progress, 4)
              const currentCount = Math.floor(easeOutQuart * target)
              setCount(currentCount)
              if (progress < 1) {
                requestAnimationFrame(animate)
              } else {
                setCount(target)
              }
            }
            animate()
          }
        })
      },
      { threshold: 0.5 }
    )

    if (elementRef.current) {
      observer.observe(elementRef.current)
    }

    return () => {
      if (elementRef.current) {
        observer.unobserve(elementRef.current)
      }
    }
  }, [target, duration, hasAnimated])

  return (
    <div ref={elementRef} className="text-5xl font-bold mb-2">
      {prefix}{count}{suffix}
    </div>
  )
}

// FAQ Item Component
function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <span className="font-semibold text-gray-900 pr-4">{question}</span>
        <ChevronDown
          className={`w-5 h-5 text-gray-500 flex-shrink-0 transition-transform ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </button>
      {isOpen && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <p className="text-gray-600 leading-relaxed">{answer}</p>
        </div>
      )}
    </div>
  )
}

export default function LandingPage() {
  const router = useRouter()
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [loading, isAuthenticated, router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-turquoise-600"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null // Will redirect
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-turquoise-500 to-turquoise-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">VeloxaRecruit</span>
            </div>
            <div className="flex items-center gap-4">
              <Link 
                href="#features" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors hidden sm:block"
              >
                Features
              </Link>
              <Link 
                href="#pricing" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors hidden sm:block"
              >
                Pricing
              </Link>
              <Link 
                href="#demo" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors hidden sm:block"
              >
                Demo
              </Link>
              <Link 
                href="#about" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors hidden sm:block"
              >
                About
              </Link>
              <Link 
                href="#faq" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors hidden sm:block"
              >
                FAQ
              </Link>
              <Link 
                href="/login" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Sign In
              </Link>
              <Link 
                href="/register" 
                className="bg-turquoise-600 text-white px-6 py-2 rounded-lg hover:bg-turquoise-700 transition-colors font-medium"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-turquoise-50/50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Zap className="w-4 h-4" />
              Powered by Veloxa Technologies Ltd
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Transform Hiring with
              <span className="block bg-gradient-to-r from-turquoise-600 to-turquoise-500 bg-clip-text text-transparent">
                AI Voice Interviews
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8 leading-relaxed">
              Conduct intelligent, automated voice interviews that analyze candidates in real-time.
              Screen faster, hire smarter, scale effortlessly.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link 
                href="/register"
                className="bg-turquoise-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-turquoise-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center gap-2"
              >
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
              <a 
                href="#demo"
                className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all flex items-center gap-2"
              >
                <Play className="w-5 h-5" />
                Watch Demo
              </a>
            </div>
            <p className="text-sm text-gray-500 mt-6">
              ⚡ No credit card required • 🎁 14-day free trial • ⚙️ Setup in 5 minutes
            </p>
            <div className="mt-8 flex items-center justify-center gap-6 text-sm text-gray-600 flex-wrap">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                <span>Cancel anytime</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                <span>No setup fees</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                <span>Full access</span>
              </div>
            </div>
          </div>

          {/* Demo Video Section */}
          <div id="demo" className="mt-12 relative max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-turquoise-100 to-yellow-50 rounded-xl p-4 border border-turquoise-200 shadow-lg">
              <div className="bg-gray-900 rounded-lg overflow-hidden shadow-md">
                <div className="relative aspect-video">
                  <iframe
                    src="https://www.youtube.com/embed/kg52RdNPbCo?autoplay=1&mute=1&loop=1&playlist=kg52RdNPbCo&controls=1&modestbranding=1&rel=0"
                    className="absolute inset-0 w-full h-full"
                    allow="autoplay; encrypted-media"
                    allowFullScreen
                    title="VeloxaRecruit Demo Video"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" id="features">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Hire Smarter
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful AI-driven features that streamline your entire recruitment process
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI Voice Interviews</h3>
              <p className="text-gray-600">
                Conduct natural, conversational interviews powered by advanced AI. Questions adapt based on candidate responses.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-yellow-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Automated CV Screening</h3>
              <p className="text-gray-600">
                Instantly analyze and rank CVs against job requirements. Save hours of manual screening time.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Candidate Analysis</h3>
              <p className="text-gray-600">
                Get comprehensive insights on candidates including skill assessments, cultural fit, and detailed reports.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-yellow-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Candidate Pipeline</h3>
              <p className="text-gray-600">
                Manage your entire hiring pipeline from application to offer with customizable stages and workflows.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Advanced Analytics and Reports</h3>
              <p className="text-gray-600">
                Track hiring metrics, interview performance, and make data-driven decisions with detailed analytics.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-yellow-300 hover:shadow-xl transition-all duration-300 bg-white transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <Workflow className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Automated Workflows</h3>
              <p className="text-gray-600">
                Set up automated email responses, interview scheduling, and candidate communications.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Built for Every Team
            </h2>
            <p className="text-xl text-gray-600">
              Whether you're a startup or enterprise, we've got you covered
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-turquoise-100 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-turquoise-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Recruiters</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Screen candidates 10x faster. Focus on building relationships while AI handles the initial assessments.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Automated candidate ranking</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Instant interview summaries</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Customizable interview questions</span>
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-yellow-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-yellow-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">HR Teams</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Streamline hiring processes and maintain consistency across all interviews with standardized AI assessments.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-yellow-600" />
                  <span>Bias-free candidate evaluation</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-yellow-600" />
                  <span>Compliance and audit trails</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-yellow-600" />
                  <span>Team collaboration tools</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Trust & Security Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Secure & Compliant
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
              Your data security and candidate privacy are our top priorities
            </p>
            <p className="text-lg text-gray-700 font-medium mb-6">
              Join 500+ companies already using VeloxaRecruit
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-white rounded-xl border border-gray-200 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-300">
              <div className="w-16 h-16 bg-turquoise-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">End-to-End Encryption</h3>
              <p className="text-gray-600">
                All candidate data is encrypted in transit and at rest using industry-standard protocols
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-xl border border-gray-200 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-300">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">GDPR Compliant</h3>
              <p className="text-gray-600">
                Fully compliant with GDPR, CCPA, and other data protection regulations worldwide
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-xl border border-gray-200 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-300">
              <div className="w-16 h-16 bg-turquoise-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="w-8 h-8 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">SOC 2 Certified</h3>
              <p className="text-gray-600">
                Enterprise-grade security with regular audits and compliance certifications
              </p>
            </div>
          </div>

          <div className="mt-12 grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200">
              <CheckCircle className="w-6 h-6 text-turquoise-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Regular Security Audits</h4>
                <p className="text-sm text-gray-600">Continuous monitoring and third-party security assessments</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200">
              <CheckCircle className="w-6 h-6 text-turquoise-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Data Retention Controls</h4>
                <p className="text-sm text-gray-600">Configurable data retention policies and automated deletion</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200">
              <CheckCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Access Controls</h4>
                <p className="text-sm text-gray-600">Role-based permissions and SSO support for enterprise</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200">
              <CheckCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">99.9% Uptime SLA</h4>
                <p className="text-sm text-gray-600">Reliable infrastructure with guaranteed availability</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Trusted by Hiring Teams Worldwide
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              See what our customers are saying about VeloxaRecruit
            </p>
            <Link 
              href="/register"
              className="inline-flex items-center gap-2 bg-turquoise-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Join Them Today
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-turquoise-50 to-white p-8 rounded-xl border border-turquoise-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-400">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "VeloxaRecruit has completely transformed our hiring process. We've reduced our time-to-hire by 75% and the AI interviews provide insights we never had before."
              </p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-turquoise-600 rounded-full flex items-center justify-center text-white font-semibold">
                  SJ
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Sarah Johnson</div>
                  <div className="text-sm text-gray-600">HR Director, TechCorp</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-yellow-50 to-white p-8 rounded-xl border border-yellow-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-yellow-400">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "The automated CV screening alone saves us 20 hours per week. Combined with the AI interviews, we're hiring better candidates faster than ever."
              </p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center text-white font-semibold">
                  MK
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Michael Kim</div>
                  <div className="text-sm text-gray-600">Recruitment Manager, StartupHub</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-turquoise-50 to-white p-8 rounded-xl border border-turquoise-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer hover:border-turquoise-400">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "As a growing company, we needed a solution that could scale. VeloxaRecruit handles everything from 10 to 1000 interviews per month effortlessly."
              </p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-turquoise-600 rounded-full flex items-center justify-center text-white font-semibold">
                  EL
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Emily Liu</div>
                  <div className="text-sm text-gray-600">Head of Talent, ScaleUp Inc</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" id="pricing">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your hiring needs. All plans include a free trial.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Starter Plan */}
            <div className="border-2 border-gray-200 rounded-xl p-8 bg-white hover:border-turquoise-300 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Starter</h3>
                <p className="text-gray-600">Perfect for small teams getting started</p>
              </div>
              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-bold text-gray-900">$49</span>
                  <span className="text-gray-600">/month</span>
                </div>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Up to 50 interviews/month</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Unlimited CV screening</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Basic analytics & reports</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Email support</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>1 job posting at a time</span>
                </li>
              </ul>
              <Link 
                href="/register?plan=starter"
                className="block w-full bg-turquoise-600 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Professional Plan - Featured */}
            <div className="border-2 border-turquoise-600 rounded-xl p-8 bg-gradient-to-br from-turquoise-50 to-white relative hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-3 hover:scale-[1.03] cursor-pointer">
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <span className="bg-yellow-400 text-gray-900 px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </span>
              </div>
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Professional</h3>
                <p className="text-gray-600">For growing teams and agencies</p>
              </div>
              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-bold text-gray-900">$149</span>
                  <span className="text-gray-600">/month</span>
                </div>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Up to 200 interviews/month</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Unlimited CV screening</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Advanced analytics & reports</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Priority email support</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>5 active job postings</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Custom interview workflows</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Team collaboration tools</span>
                </li>
              </ul>
              <Link 
                href="/register?plan=professional"
                className="block w-full bg-turquoise-600 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="border-2 border-gray-200 rounded-xl p-8 bg-white hover:border-turquoise-300 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-2 hover:scale-[1.02] cursor-pointer">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Enterprise</h3>
                <p className="text-gray-600">For large organizations</p>
              </div>
              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-bold text-gray-900">Custom</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">Contact us for pricing</p>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Unlimited interviews</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Unlimited CV screening</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Custom analytics & dashboards</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>24/7 dedicated support</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Unlimited job postings</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>API access & integrations</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>SSO & advanced security</span>
                </li>
                <li className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
                  <span>Custom onboarding & training</span>
                </li>
              </ul>
              <Link 
                href="/register"
                className="block w-full bg-gray-900 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
              >
                Contact Sales
              </Link>
            </div>
          </div>

          <div className="text-center mt-12">
            <p className="text-lg font-semibold text-gray-900 mb-2">
              🎁 All plans include a 14-day free trial
            </p>
            <p className="text-gray-600 mb-6">
              No credit card required • Full access to all features • Cancel anytime
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link 
                href="/register"
                className="bg-turquoise-600 text-white px-10 py-4 rounded-lg text-lg font-semibold hover:bg-turquoise-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center gap-2"
              >
                Start Your Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link 
                href="#"
                className="text-turquoise-600 hover:text-turquoise-700 font-medium underline"
              >
                Need help choosing? Contact our team
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-turquoise-600 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">See the Results for Yourself</h2>
            <p className="text-turquoise-100 text-lg">Join thousands of companies transforming their hiring process</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 text-center mb-12">
            <div className="transform transition-all duration-300 hover:scale-105">
              <AnimatedCounter target={10} suffix="x" />
              <div className="text-turquoise-100 text-lg">Faster Screening</div>
            </div>
            <div className="transform transition-all duration-300 hover:scale-105">
              <AnimatedCounter target={95} suffix="%" />
              <div className="text-turquoise-100 text-lg">Time Saved</div>
            </div>
            <div className="transform transition-all duration-300 hover:scale-105">
              <div className="text-5xl font-bold mb-2">24/7</div>
              <div className="text-turquoise-100 text-lg">Always Available</div>
            </div>
          </div>
          <div className="text-center">
            <Link 
              href="/register"
              className="inline-flex items-center gap-2 bg-white text-turquoise-600 px-10 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* About Us Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" id="about">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              About Veloxa Technologies Ltd
            </h2>
            <div className="w-24 h-1 bg-gradient-to-r from-turquoise-500 to-yellow-400 mx-auto rounded"></div>
          </div>

          <div className="prose prose-lg max-w-none">
            <div className="grid md:grid-cols-2 gap-8 mb-12">
              <div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">Our Mission</h3>
                <p className="text-gray-600 leading-relaxed">
                  At Veloxa Technologies, we're revolutionizing the recruitment industry by harnessing the power of artificial intelligence. 
                  Our mission is to make hiring faster, smarter, and more efficient for organizations of all sizes.
                </p>
              </div>
              <div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">Why VeloxaRecruit?</h3>
                <p className="text-gray-600 leading-relaxed">
                  VeloxaRecruit combines cutting-edge AI technology with intuitive design to deliver a recruitment platform that 
                  eliminates bias, saves time, and helps you find the best candidates faster than ever before.
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-turquoise-50 to-yellow-50 rounded-xl p-8 border border-turquoise-200">
              <h3 className="text-2xl font-semibold text-gray-900 mb-4">Key Benefits</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-turquoise-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">AI-Powered Intelligence</h4>
                    <p className="text-sm text-gray-600">Advanced algorithms analyze candidates with precision and fairness</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-turquoise-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Time Efficiency</h4>
                    <p className="text-sm text-gray-600">Reduce time-to-hire by up to 95% with automated screening</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Bias-Free Hiring</h4>
                    <p className="text-sm text-gray-600">Objective candidate evaluation ensures fair and inclusive hiring</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Scalable Solution</h4>
                    <p className="text-sm text-gray-600">Grow from startup to enterprise with flexible plans</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-12 text-center">
              <p className="text-lg text-gray-700 mb-4 font-medium">
                Ready to revolutionize your hiring process?
              </p>
              <Link 
                href="/register"
                className="inline-flex items-center gap-2 bg-turquoise-600 text-white px-10 py-4 rounded-lg text-lg font-semibold hover:bg-turquoise-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Start Your Free Trial Today
                <ArrowRight className="w-5 h-5" />
              </Link>
              <p className="text-sm text-gray-500 mt-4">
                No credit card required • Setup in 5 minutes
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" id="faq">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need to know about VeloxaRecruit
            </p>
          </div>

          <div className="space-y-4">
            {/* FAQ Item 1 */}
            <FAQItem
              question="How does AI interviewing work?"
              answer="VeloxaRecruit uses advanced AI to conduct natural, conversational interviews. The AI asks questions based on the job description and candidate's CV, adapts follow-up questions based on responses, and analyzes answers in real-time. You receive a detailed report with insights, scores, and recommendations."
            />

            {/* FAQ Item 2 */}
            <FAQItem
              question="Is the AI biased against candidates?"
              answer="No. Our AI is designed to be objective and bias-free. We use structured evaluation criteria based solely on job requirements and candidate qualifications. The system is regularly audited for fairness, and all interviews are recorded for transparency and review."
            />

            {/* FAQ Item 3 */}
            <FAQItem
              question="What happens to candidate data?"
              answer="Candidate data is encrypted and stored securely. We're GDPR and CCPA compliant, and candidates can request access to or deletion of their data at any time. You control data retention policies, and we never share candidate information with third parties."
            />

            {/* FAQ Item 4 */}
            <FAQItem
              question="Can we customize interview questions?"
              answer="Yes! You can customize interview questions by job role, add your own questions, set difficulty levels, and configure the interview flow. Our AI will generate contextually relevant follow-up questions based on your specifications."
            />

            {/* FAQ Item 5 */}
            <FAQItem
              question="Do you integrate with ATS systems?"
              answer="Yes, VeloxaRecruit offers API access for integration with popular ATS systems. We also support webhook integrations and can work with most systems that support standard data formats. Enterprise plans include dedicated integration support."
            />

            {/* FAQ Item 6 */}
            <FAQItem
              question="What languages are supported?"
              answer="Currently, interviews are conducted in English. However, our AI can analyze CVs in multiple languages and we're continuously expanding language support. Contact us for specific language requirements."
            />

            {/* FAQ Item 7 */}
            <FAQItem
              question="How do I cancel my subscription?"
              answer="You can cancel your subscription at any time from your account settings. There are no cancellation fees, and you'll retain access until the end of your billing period. Your data will be available for export for 30 days after cancellation."
            />

            {/* FAQ Item 8 */}
            <FAQItem
              question="Is there a free trial?"
              answer="Yes! All plans include a 14-day free trial with full access to all features. No credit card required to start. You can upgrade, downgrade, or cancel anytime during the trial period."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-turquoise-50 to-yellow-50 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-turquoise-100/20 to-yellow-100/20"></div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            Limited Time: 14-Day Free Trial
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Ready to Transform Your Hiring?
          </h2>
          <p className="text-xl text-gray-600 mb-4">
            Join thousands of companies using AI to hire faster and smarter.
          </p>
          <p className="text-lg text-gray-700 mb-8 font-medium">
            Start your free trial today. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-6">
            <Link 
              href="/register"
              className="bg-turquoise-600 text-white px-10 py-5 rounded-lg text-xl font-bold hover:bg-turquoise-700 transition-all shadow-2xl hover:shadow-3xl transform hover:-translate-y-1 flex items-center gap-2 w-full sm:w-auto justify-center"
            >
              Start Free Trial Now
              <ArrowRight className="w-6 h-6" />
            </Link>
            <Link 
              href="/login"
              className="bg-white text-gray-900 border-2 border-gray-300 px-8 py-5 rounded-lg text-lg font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all w-full sm:w-auto"
            >
              Sign In
            </Link>
          </div>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-600 flex-wrap">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
              <span>Cancel anytime</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-turquoise-600" />
              <span>Full access included</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-turquoise-500 to-turquoise-600 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-white font-bold">VeloxaRecruit</span>
              </div>
              <p className="text-sm text-gray-400">
                By Veloxa Technologies Ltd
              </p>
              <p className="text-sm text-gray-400 mt-1">
                The future of intelligent recruitment
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="#features" className="hover:text-turquoise-400 transition-colors">Features</Link></li>
                <li><Link href="#pricing" className="hover:text-turquoise-400 transition-colors">Pricing</Link></li>
                <li><Link href="#demo" className="hover:text-turquoise-400 transition-colors">Demo</Link></li>
                <li><Link href="#faq" className="hover:text-turquoise-400 transition-colors">FAQ</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="#about" className="hover:text-turquoise-400 transition-colors">About Us</Link></li>
                <li><Link href="#" className="hover:text-turquoise-400 transition-colors">Blog</Link></li>
                <li><Link href="#" className="hover:text-turquoise-400 transition-colors">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="#" className="hover:text-turquoise-400 transition-colors">Documentation</Link></li>
                <li><Link href="#" className="hover:text-turquoise-400 transition-colors">Help Center</Link></li>
                <li><Link href="#" className="hover:text-turquoise-400 transition-colors">API</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
            © {new Date().getFullYear()} Veloxa Technologies Ltd. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
