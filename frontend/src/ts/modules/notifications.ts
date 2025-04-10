/**
 * Notifications Module - Handles notification display and management
 */

import { NotificationType } from '../types';

/**
 * Create notification container if it doesn't exist
 */
function createNotificationContainer(): HTMLElement {
    const existingContainer = document.getElementById('notification-container');
    if (existingContainer) return existingContainer;
    
    const container = document.createElement('div');
    container.id = 'notification-container';
    document.body.appendChild(container);
    return container;
}

/**
 * Notification system initialization
 */
export function initNotifications(): void {
    // Create container if it doesn't exist
    createNotificationContainer();
    
    // Close existing notifications when clicked
    document.addEventListener('click', function(e) {
        const target = e.target as HTMLElement;
        if (target.classList.contains('close-notification') || 
            target.closest('.close-notification')) {
            const notification = target.closest('.notification');
            if (notification) {
                closeNotification(notification as HTMLElement);
            }
        }
    });
}

/**
 * Close a notification
 */
export function closeNotification(notification: HTMLElement): void {
    notification.classList.remove('visible');
    setTimeout(() => {
        notification.remove();
    }, 300);
}

/**
 * Show a notification message
 */
export function showNotification(message: string, type: NotificationType = 'info', autoHide: boolean = true, duration: number = 5000): void {
    const notificationContainer = document.getElementById('notification-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <p>${message}</p>
            <button class="close-notification" aria-label="Close notification">&times;</button>
        </div>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Add event listener to close button
    const closeButton = notification.querySelector('.close-notification');
    if (closeButton) {
        closeButton.addEventListener('click', () => closeNotification(notification));
    }
    
    // Auto-hide after duration
    if (autoHide) {
        setTimeout(() => {
            if (notification.parentNode) {
                closeNotification(notification);
            }
        }, duration);
    }
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('visible');
    }, 10);
} 