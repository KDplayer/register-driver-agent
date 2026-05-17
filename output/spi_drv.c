#include "spi_regs.h"

void SPI_Init(SPI_Config_t* config)
{
    // Calculate baud rate divider
    uint32_t br_value = (SystemCoreClock / config->baudrate) - 1;
    
    // Configure CR1 register
    uint32_t cr1 = 0;
    cr1 |= (br_value << SPI_CR1_BR_POS);
    cr1 |= (config->cpol ? SPI_CR1_CPOL : 0);
    cr1 |= (config->cpha ? SPI_CR1_CPHA : 0);
    cr1 |= SPI_CR1_MSTR;  // Master mode
    SPI_CR1 = cr1;
    
    // Enable SPI
    SPI_CR1 |= SPI_CR1_SPE;
}

uint8_t SPI_TransmitReceive(uint8_t data)
{
    // Wait for TX buffer empty
    while(!(SPI_SR & SPI_SR_TXE));
    SPI_DR = data;
    
    // Wait for RX buffer not empty
    while(!(SPI_SR & SPI_SR_RXNE));
    return SPI_DR;
}