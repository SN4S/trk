export interface Message {
  id: number
  text: string
  time: string
  isOut: boolean
  status?: 'sent' | 'delivered' | 'read'
  isSystem?: boolean
}

export interface Chat {
  id: number
  name: string
  avatar: string
  lastMessage: string
  time: string
  unread: number
  online: boolean
  status: 'open' | 'pending' | 'resolved'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  tag: string
  email: string
  phone: string
  location: string
  joined: string
  agent: string
  messages: Message[]
}

const avatarColors = [
  '#e05252', '#e07a52', '#e0c252', '#52c2e0',
  '#5272e0', '#a052e0', '#e052b6', '#52e09a',
]

// function hsl(str: string): string {
//   let hash = 0
//   for (let i = 0; i < str.length; i++) {
//     hash = str.charCodeAt(i) + ((hash << 5) - hash)
//   }
//   return avatarColors[Math.abs(hash) % avatarColors.length]
// }

function initials(name: string): string {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

export const useChats = () => {
  const chats = ref<Chat[]>([
    {
      id: 1,
      name: 'Alice Johnson',
      avatar: hsl('Alice Johnson'),
      lastMessage: 'My order still hasn\'t arrived after 2 weeks...',
      time: '10:42',
      unread: 3,
      online: true,
      status: 'open',
      priority: 'urgent',
      tag: 'Shipping',
      email: 'alice.j@email.com',
      phone: '+1 (555) 234-5678',
      location: 'San Francisco, CA',
      joined: 'Mar 2023',
      agent: 'Sarah K.',
      messages: [
        { id: 1, text: 'Hello! I placed an order 2 weeks ago and it still hasn\'t arrived.', time: '10:15', isOut: false },
        { id: 2, text: 'Hi Alice! I\'m sorry to hear that. Can you share your order number?', time: '10:18', isOut: true, status: 'read' },
        { id: 3, text: 'Sure, it\'s #ORD-48291', time: '10:20', isOut: false },
        { id: 4, text: 'Thank you! Let me look that up for you right now.', time: '10:21', isOut: true, status: 'read' },
        { id: 5, text: 'I can see your order is currently stuck at the regional sorting facility. I\'ll escalate this immediately.', time: '10:35', isOut: true, status: 'delivered' },
        { id: 6, text: 'My order still hasn\'t arrived after 2 weeks...', time: '10:42', isOut: false },
      ],
    },
    {
      id: 2,
      name: 'Bob Martinez',
      avatar: hsl('Bob Martinez'),
      lastMessage: 'Thanks for the quick help! 👍',
      time: '09:55',
      unread: 0,
      online: false,
      status: 'resolved',
      priority: 'low',
      tag: 'Billing',
      email: 'bob.m@email.com',
      phone: '+1 (555) 876-5432',
      location: 'Austin, TX',
      joined: 'Jan 2024',
      agent: 'Mike T.',
      messages: [
        { id: 1, text: 'I was charged twice for my subscription last month.', time: '09:30', isOut: false },
        { id: 2, text: 'Hello Bob! I see the double charge. I\'ll process a refund immediately.', time: '09:35', isOut: true, status: 'read' },
        { id: 3, text: 'The refund has been initiated. It should appear within 3-5 business days.', time: '09:50', isOut: true, status: 'read' },
        { id: 4, text: 'Thanks for the quick help! 👍', time: '09:55', isOut: false },
      ],
    },
    {
      id: 3,
      name: 'Carol White',
      avatar: hsl('Carol White'),
      lastMessage: 'Can I upgrade my plan mid-cycle?',
      time: '09:10',
      unread: 1,
      online: true,
      status: 'pending',
      priority: 'normal',
      tag: 'Account',
      email: 'carol.w@email.com',
      phone: '+1 (555) 345-6789',
      location: 'New York, NY',
      joined: 'Jun 2022',
      agent: 'Sarah K.',
      messages: [
        { id: 1, text: 'Hi! I\'m on the Basic plan and need more storage.', time: '09:00', isOut: false },
        { id: 2, text: 'Hi Carol! Of course, we can upgrade you. Which plan are you interested in?', time: '09:05', isOut: true, status: 'read' },
        { id: 3, text: 'Can I upgrade my plan mid-cycle?', time: '09:10', isOut: false },
      ],
    },
    {
      id: 4,
      name: 'David Lee',
      avatar: hsl('David Lee'),
      lastMessage: 'The app keeps crashing on iOS 17',
      time: 'Yesterday',
      unread: 5,
      online: false,
      status: 'open',
      priority: 'high',
      tag: 'Technical',
      email: 'david.l@email.com',
      phone: '+1 (555) 567-8901',
      location: 'Seattle, WA',
      joined: 'Nov 2023',
      agent: 'Alex R.',
      messages: [
        { id: 1, text: 'Hey, your iOS app is completely broken on my iPhone 15 Pro.', time: 'Yesterday 14:20', isOut: false },
        { id: 2, text: 'Hi David! We\'re aware of some iOS 17 compatibility issues. Can you share your app version?', time: 'Yesterday 14:45', isOut: true, status: 'read' },
        { id: 3, text: 'Version 3.2.1 — crashes every time I try to open a document', time: 'Yesterday 15:00', isOut: false },
        { id: 4, text: 'The app keeps crashing on iOS 17', time: 'Yesterday 18:30', isOut: false },
      ],
    },
    {
      id: 5,
      name: 'Eva Chen',
      avatar: hsl('Eva Chen'),
      lastMessage: 'Refund received, thank you!',
      time: 'Yesterday',
      unread: 0,
      online: true,
      status: 'resolved',
      priority: 'normal',
      tag: 'Refund',
      email: 'eva.c@email.com',
      phone: '+1 (555) 678-9012',
      location: 'Chicago, IL',
      joined: 'Aug 2021',
      agent: 'Mike T.',
      messages: [
        { id: 1, text: 'I returned my item last week and haven\'t gotten a refund.', time: 'Yesterday 10:00', isOut: false },
        { id: 2, text: 'Hi Eva! I\'ll process that refund for you now.', time: 'Yesterday 10:15', isOut: true, status: 'read' },
        { id: 3, text: 'Refund received, thank you!', time: 'Yesterday 16:00', isOut: false },
      ],
    },
    {
      id: 6,
      name: 'Frank Brown',
      avatar: hsl('Frank Brown'),
      lastMessage: 'How do I export my data?',
      time: 'Mon',
      unread: 2,
      online: false,
      status: 'pending',
      priority: 'low',
      tag: 'General',
      email: 'frank.b@email.com',
      phone: '+1 (555) 789-0123',
      location: 'Boston, MA',
      joined: 'Feb 2024',
      agent: 'Alex R.',
      messages: [
        { id: 1, text: 'Is there a way to export all my data?', time: 'Mon 11:00', isOut: false },
        { id: 2, text: 'How do I export my data?', time: 'Mon 11:30', isOut: false },
      ],
    },
    {
      id: 7,
      name: 'Grace Kim',
      avatar: hsl('Grace Kim'),
      lastMessage: 'My password reset email never came',
      time: 'Sun',
      unread: 0,
      online: true,
      status: 'open',
      priority: 'high',
      tag: 'Account',
      email: 'grace.k@email.com',
      phone: '+1 (555) 890-1234',
      location: 'Los Angeles, CA',
      joined: 'Dec 2022',
      agent: 'Sarah K.',
      messages: [
        { id: 1, text: 'I can\'t log into my account', time: 'Sun 15:00', isOut: false },
        { id: 2, text: 'We can reset your password. What email did you use?', time: 'Sun 15:10', isOut: true, status: 'read' },
        { id: 3, text: 'My password reset email never came', time: 'Sun 15:45', isOut: false },
      ],
    },
    {
      id: 8,
      name: 'Henry Wilson',
      avatar: hsl('Henry Wilson'),
      lastMessage: 'Got it, will try that now',
      time: 'Sat',
      unread: 0,
      online: false,
      status: 'resolved',
      priority: 'normal',
      tag: 'Technical',
      email: 'henry.w@email.com',
      phone: '+1 (555) 901-2345',
      location: 'Denver, CO',
      joined: 'May 2023',
      agent: 'Alex R.',
      messages: [
        { id: 1, text: 'The dashboard is not loading correctly', time: 'Sat 09:00', isOut: false },
        { id: 2, text: 'Try clearing your cache and hard-refreshing (Ctrl+Shift+R)', time: 'Sat 09:20', isOut: true, status: 'read' },
        { id: 3, text: 'Got it, will try that now', time: 'Sat 09:25', isOut: false },
      ],
    },
  ])

  const selectedChatId = ref<number>(1)

  const selectedChat = computed(() =>
    chats.value.find(c => c.id === selectedChatId.value) ?? null
  )

  function getInitials(name: string) { return initials(name) }

  return { chats, selectedChatId, selectedChat, getInitials }
}
