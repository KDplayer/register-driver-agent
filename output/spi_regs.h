#ifndef SPI_REGS_H
#define SPI_REGS_H

/* Register base address */
#define SPI1_BASE           0x40013000

/* Control Register 1 (CR1) - offset 0x00 */
#define SPI_CR1              (*(volatile uint32_t*)(SPI1_BASE + 0x00))
#define SPI_CR1_BR_POS       3
#define SPI_CR1_BR_MASK      (0x7 << 3)
#define SPI_CR1_SPE          (1 << 6)
#define SPI_CR1_MSTR         (1 << 2)
#define SPI_CR1_CPOL         (1 << 1)
#define SPI_CR1_CPHA         (1 << 0)

/* Status Register (SR) - offset 0x08 */
#define SPI_SR               (*(volatile uint32_t*)(SPI1_BASE + 0x08))
#define SPI_SR_TXE           (1 << 1)
#define SPI_SR_RXNE          (1 << 0)

#endif