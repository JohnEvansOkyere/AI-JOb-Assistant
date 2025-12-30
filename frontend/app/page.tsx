/**
 * Landing Page
 * Public-facing homepage inspired by n8n design
 */

'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useEffect } from 'react'
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
  Workflow
} from 'lucide-react'
import Link from 'next/link'

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
              No credit card required • Free trial • Setup in minutes
            </p>
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
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI Voice Interviews</h3>
              <p className="text-gray-600">
                Conduct natural, conversational interviews powered by advanced AI. Questions adapt based on candidate responses.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Automated CV Screening</h3>
              <p className="text-gray-600">
                Instantly analyze and rank CVs against job requirements. Save hours of manual screening time.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Candidate Analysis</h3>
              <p className="text-gray-600">
                Get comprehensive insights on candidates including skill assessments, cultural fit, and detailed reports.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Candidate Pipeline</h3>
              <p className="text-gray-600">
                Manage your entire hiring pipeline from application to offer with customizable stages and workflows.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
              <div className="w-12 h-12 bg-turquoise-100 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-turquoise-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Analytics & Reports</h3>
              <p className="text-gray-600">
                Track hiring metrics, interview performance, and make data-driven decisions with detailed analytics.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-xl border border-gray-200 hover:border-turquoise-300 hover:shadow-lg transition-all bg-white">
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
            <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm">
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

            <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm">
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
            <div className="border-2 border-gray-200 rounded-xl p-8 bg-white hover:border-turquoise-300 transition-all hover:shadow-lg">
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
                href="/register"
                className="block w-full bg-turquoise-600 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Professional Plan - Featured */}
            <div className="border-2 border-turquoise-600 rounded-xl p-8 bg-gradient-to-br from-turquoise-50 to-white relative hover:shadow-xl transition-all">
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
                href="/register"
                className="block w-full bg-turquoise-600 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="border-2 border-gray-200 rounded-xl p-8 bg-white hover:border-turquoise-300 transition-all hover:shadow-lg">
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
            <p className="text-gray-600 mb-4">
              All plans include a 14-day free trial. No credit card required.
            </p>
            <p className="text-sm text-gray-500">
              Need help choosing? <Link href="#" className="text-turquoise-600 hover:underline">Contact our team</Link>
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-turquoise-600 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-5xl font-bold mb-2">10x</div>
              <div className="text-turquoise-100 text-lg">Faster Screening</div>
            </div>
            <div>
              <div className="text-5xl font-bold mb-2">95%</div>
              <div className="text-turquoise-100 text-lg">Time Saved</div>
            </div>
            <div>
              <div className="text-5xl font-bold mb-2">24/7</div>
              <div className="text-turquoise-100 text-lg">Always Available</div>
            </div>
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
              <Link 
                href="/register"
                className="inline-block bg-turquoise-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-turquoise-700 transition-colors"
              >
                Start Your Free Trial Today
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-turquoise-50 to-yellow-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Ready to Transform Your Hiring?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of companies using AI to hire faster and smarter.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/register"
              className="bg-turquoise-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-turquoise-700 transition-all shadow-lg hover:shadow-xl"
            >
              Start Free Trial
            </Link>
            <Link 
              href="/login"
              className="bg-white text-gray-900 border-2 border-gray-300 px-8 py-4 rounded-lg text-lg font-semibold hover:border-gray-400 transition-all"
            >
              Sign In
            </Link>
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
