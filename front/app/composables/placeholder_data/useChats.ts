export interface Message {
    id: number
    user_name: string
    user_id: number
    text: string
    time: string
    isOut: boolean
    status?: 'sent' | 'delivered' | 'read'
    isSystem?: boolean
}

export interface Ticket {
    ticket_id: number
    ticket_code: string
    chat_id: number
    theme: string
    message: string
    user_id: number
    user_name: string
    submit_date: number
    last_updated: number
    status: string
}

export interface Group {
    id: number
    name: string
    avatar: string
    messages: Message[]
}

export const groups: Group[] = [
    {
        id: 1,
        name: 'xFitness',
        avatar: 'https://placehold.co/100x100/blue/white?text=XF',
        messages: [
            {
                id: 101,
                user_name: 'Admin',
                user_id: 1,
                text: 'Добрий день! Чим можемо допомогти?',
                time: '13:15',
                isOut: true,
                status: 'read'
            },
            {
                id: 102,
                user_name: 'Клієнт',
                user_id: 42,
                text: 'Знову пробеми з виводом зоображення',
                time: '13:30',
                isOut: false,
                status: 'read'
            }
        ]
    },
    {
        id: 2,
        name: 'CRM',
        avatar: 'https://placehold.co/100x100/green/white?text=CRM',
        messages: [
            {
                id: 201,
                user_name: 'System',
                user_id: 0,
                text: 'Користувач створив новий запит',
                time: '12:00',
                isOut: false,
                isSystem: true
            },
            {
                id: 202,
                user_name: 'Менеджер',
                user_id: 2,
                text: 'Вітаю. Бачу вашу заявку, зараз перевірю деталі.',
                time: '12:10',
                isOut: true,
                status: 'read'
            },
            {
                id: 203,
                user_name: 'Іван',
                user_id: 55,
                text: 'Проблеми з оплатою після 30.06',
                time: '13:30',
                isOut: false,
                status: 'delivered'
            }
        ]
    },
    {
        id: 3,
        name: 'Test',
        avatar: 'https://placehold.co/100x100/orange/white?text=T',
        messages: [
            {
                id: 301,
                user_name: 'Tester 1',
                user_id: 99,
                text: 'ping',
                time: '13:28',
                isOut: false,
                status: 'read'
            },
            {
                id: 302,
                user_name: 'Tester 2',
                user_id: 100,
                text: 'pong',
                time: '13:29',
                isOut: true,
                status: 'read'
            },
            {
                id: 303,
                user_name: 'Tester 1',
                user_id: 99,
                text: 'test message always, the best message',
                time: '13:30',
                isOut: false,
                status: 'read'
            }
        ]
    },
    {
        id: 4,
        name: 'xProSupportTest',
        avatar: 'https://placehold.co/100x100/purple/white?text=xPro',
        messages: [
            {
                id: 401,
                user_name: 'System',
                user_id: 0,
                text: 'Ticket #Oleksandrxprosupport-27 created',
                time: '10:00',
                isOut: false,
                isSystem: true
            },
            {
                id: 402,
                user_name: 'Support Bot',
                user_id: 0,
                text: 'Дякуємо за звернення! Оператор скоро підключиться.',
                time: '10:01',
                isOut: true,
                status: 'delivered',
                isSystem: true
            },
            {
                id: 403,
                user_name: 'Oleksandr',
                user_id: 77,
                text: '💬 Додаткова інформація по тікету #Oleksandrxprosupport-27',
                time: '13:30',
                isOut: false,
                status: 'sent'
            }
        ]
    }
];

export const ticket: Ticket =
    {
        ticket_id: 1,
        ticket_code: 'seq-1',
        chat_id: 1,
        theme: "tewst theme",
        message: "everything is dead",
        user_id: 1,
        user_name: 'sn4s',
        submit_date: 20,
        last_updated: 20,
        status: 'open'
    }

export const ticket2: Ticket =
    {
        ticket_id: 2,
        ticket_code: 'seq-2',
        chat_id: 1,
        theme: "tewst theme",
        message: "everything is dead",
        user_id: 1,
        user_name: 'sn4s',
        submit_date: 20,
        last_updated: 20,
        status: 'pending'
    }
export const ticket3: Ticket =
    {
        ticket_id: 3,
        ticket_code: 'seq-3',
        chat_id: 1,
        theme: "tewst theme",
        message: "everything is dead",
        user_id: 1,
        user_name: 'sn4s',
        submit_date: 20,
        last_updated: 20,
        status: 'closed'
    }