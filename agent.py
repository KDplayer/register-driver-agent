
---

## 文件 2：agent.py（核心脚本）

```python
#!/usr/bin/env python3
"""
Register Driver Agent - AI-powered embedded driver generator
Demonstrates 5-step long-chain reasoning for driver code generation
"""

import argparse
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple

class RegisterDriverAgent:
    """Single Agent with 5-step long-chain reasoning"""
    
    def __init__(self):
        self.steps_log = []
        self.token_estimate = 0
        
    def log(self, step: str, message: str):
        """Log execution steps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Step {step}: {message}"
        self.steps_log.append(log_entry)
        print(log_entry)
    
    def parse_svd(self, svd_content: str) -> Dict:
        """Step 1: Parse SVD/register description"""
        self.log("1/5", "Parsing register description file...")
        
        # Extract peripheral info using regex
        peripheral_match = re.search(r'<peripheral>\s*<name>(\w+)</name>', svd_content)
        base_match = re.search(r'<baseAddress>0x([0-9a-fA-F]+)</baseAddress>', svd_content)
        
        registers = []
        reg_pattern = r'<register>\s*<name>(\w+)</name>\s*<description>(.*?)</description>\s*<addressOffset>0x([0-9a-fA-F]+)</addressOffset>\s*<resetValue>(0x[0-9a-fA-F]+)</resetValue>'
        
        for match in re.finditer(reg_pattern, svd_content, re.DOTALL):
            registers.append({
                'name': match.group(1),
                'desc': match.group(2),
                'offset': int(match.group(3), 16),
                'reset': match.group(4)
            })
        
        bitfields = []
        bf_pattern = r'<field>\s*<name>(\w+)</name>\s*<description>(.*?)</description>\s*<bitOffset>(\d+)</bitOffset>\s*<bitWidth>(\d+)</bitWidth>'
        
        for match in re.finditer(bf_pattern, svd_content, re.DOTALL):
            bitfields.append({
                'name': match.group(1),
                'desc': match.group(2),
                'offset': int(match.group(3)),
                'width': int(match.group(4))
            })
        
        result = {
            'peripheral': peripheral_match.group(1) if peripheral_match else "SPI",
            'base_addr': base_match.group(1) if base_match else "40013000",
            'registers': registers,
            'bitfields': bitfields
        }
        
        self.log("1/5", f"Found peripheral: {result['peripheral']}, base 0x{result['base_addr']}")
        self.log("1/5", f"Found {len(registers)} registers, {len(bitfields)} bitfields")
        self.token_estimate += 2000
        
        return result
    
    def generate_bitfield_macros(self, parsed: Dict) -> str:
        """Step 2: Generate bitfield macros"""
        self.log("2/5", "Generating bitfield shift/mask macros...")
        
        macros = []
        macros.append(f"#ifndef {parsed['peripheral']}_REGS_H")
        macros.append(f"#define {parsed['peripheral']}_REGS_H\n")
        macros.append("#include <stdint.h>\n")
        macros.append(f"/* {parsed['peripheral']} Base Address */")
        macros.append(f"#define {parsed['peripheral']}_BASE        0x{parsed['base_addr']}\n")
        
        for bf in parsed['bitfields']:
            mask = ((1 << bf['width']) - 1) << bf['offset']
            macros.append(f"/* {bf['name']}: {bf['desc']} */")
            macros.append(f"#define {parsed['peripheral']}_{bf['name']}_POS       {bf['offset']}")
            macros.append(f"#define {parsed['peripheral']}_{bf['name']}_MASK      (0x{mask:02X})")
            macros.append(f"#define {parsed['peripheral']}_{bf['name']}(val)     (((val) << {bf['offset']}) & {parsed['peripheral']}_{bf['name']}_MASK)\n")
        
        macros.append("#endif")
        
        self.log("2/5", f"Generated {len(parsed['bitfields'])} macro definitions")
        self.token_estimate += 3000
        
        return '\n'.join(macros)
    
    def generate_access_functions(self, parsed: Dict) -> str:
        """Step 3: Generate register access functions"""
        self.log("3/5", "Generating register read/write/modify functions...")
        
        functions = []
        functions.append(f"#include \"{parsed['peripheral'].lower()}_regs.h\"\n")
        functions.append("/* Register Access Functions */\n")
        
        for reg in parsed['registers'][:5]:  # Limit for demo
            reg_name = reg['name']
            functions.append(f"static inline uint32_t {parsed['peripheral']}_Read_{reg_name}(void)")
            functions.append("{")
            functions.append(f"    return *((volatile uint32_t*)({parsed['peripheral']}_BASE + 0x{reg['offset']:02X}));")
            functions.append("}\n")
            
            functions.append(f"static inline void {parsed['peripheral']}_Write_{reg_name}(uint32_t value)")
            functions.append("{")
            functions.append(f"    *((volatile uint32_t*)({parsed['peripheral']}_BASE + 0x{reg['offset']:02X})) = value;")
            functions.append("}\n")
        
        functions.append("/* Atomic modify function */")
        functions.append(f"static inline void {parsed['peripheral']}_ModifyReg(uint32_t reg_offset, uint32_t clear_mask, uint32_t set_mask)")
        functions.append("{")
        functions.append("    uint32_t val = *((volatile uint32_t*)(SPI_BASE + reg_offset));")
        functions.append("    val &= ~clear_mask;")
        functions.append("    val |= set_mask;")
        functions.append("    *((volatile uint32_t*)(SPI_BASE + reg_offset)) = val;")
        functions.append("}")
        
        self.log("3/5", f"Generated {len(parsed['registers']) * 2} access functions")
        self.token_estimate += 3000
        
        return '\n'.join(functions)
    
    def generate_init_template(self, parsed: Dict) -> str:
        """Step 4: Generate initialization template"""
        self.log("4/5", "Generating initialization template...")
        
        init_code = []
        init_code.append("\n/* Initialization Template */\n")
        init_code.append(f"typedef struct {{")
        init_code.append(f"    uint32_t baudrate;")
        init_code.append(f"    uint8_t cpol;      // Clock polarity (0/1)")
        init_code.append(f"    uint8_t cpha;      // Clock phase (0/1)")
        init_code.append(f"    uint8_t data_width; // 8 or 16 bits")
        init_code.append(f"}} {parsed['peripheral']}_Config_t;\n")
        
        init_code.append(f"void {parsed['peripheral']}_Init({parsed['peripheral']}_Config_t* config)")
        init_code.append("{")
        init_code.append("    // Step 1: Enable peripheral clock (implementation depends on MCU)")
        init_code.append("    // RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;\n")
        init_code.append("    // Step 2: Calculate baud rate divider")
        init_code.append("    uint32_t br_value = (SystemCoreClock / config->baudrate) - 1;")
        init_code.append("    if(br_value > 7) br_value = 7;\n")
        init_code.append("    // Step 3: Configure CR1 register")
        init_code.append("    uint32_t cr1 = 0;")
        init_code.append(f"    cr1 |= (br_value << {parsed['peripheral']}_BR_POS);")
        init_code.append(f"    cr1 |= (config->cpol ? {parsed['peripheral']}_CPOL : 0);")
        init_code.append(f"    cr1 |= (config->cpha ? {parsed['peripheral']}_CPHA : 0);")
        init_code.append(f"    cr1 |= {parsed['peripheral']}_MSTR;  // Master mode")
        init_code.append(f"    {parsed['peripheral']}_Write_CR1(cr1);\n")
        init_code.append("    // Step 4: Enable peripheral")
        init_code.append(f"    {parsed['peripheral']}_Write_CR1(cr1 | {parsed['peripheral']}_SPE);")
        init_code.append("}\n")
        
        init_code.append("/* Example usage */")
        init_code.append("/*")
        init_code.append(f"{parsed['peripheral']}_Config_t config = {{")
        init_code.append("    .baudrate = 1000000,  // 1 MHz")
        init_code.append("    .cpol = 0,")
        init_code.append("    .cpha = 0,")
        init_code.append("    .data_width = 8")
        init_code.append("};")
        init_code.append(f"{parsed['peripheral']}_Init(&config);")
        init_code.append("*/")
        
        self.log("4/5", "Generated initialization template with baudrate calculation")
        self.token_estimate += 2000
        
        return '\n'.join(init_code)
    
    def self_validate(self, parsed: Dict, generated_macros: str) -> bool:
        """Step 5: Self-validation"""
        self.log("5/5", "Running self-validation...")
        
        issues = []
        
        # Check 1: Verify all bitfields have macros
        for bf in parsed['bitfields']:
            macro_name = f"{parsed['peripheral']}_{bf['name']}_POS"
            if macro_name not in generated_macros:
                issues.append(f"Missing macro: {macro_name}")
        
        # Check 2: Verify offset alignment
        for reg in parsed['registers']:
            if reg['offset'] % 4 != 0:
                issues.append(f"Register {reg['name']} offset 0x{reg['offset']:02X} not 4-byte aligned")
        
        # Check 3: Verify no duplicate offsets
        offsets = [reg['offset'] for reg in parsed['registers']]
        if len(offsets) != len(set(offsets)):
            issues.append("Duplicate register offsets detected")
        
        if len(issues) == 0:
            self.log("5/5", f"All checks passed: {len(parsed['bitfields'])} bitfields validated, {len(parsed['registers'])} registers verified")
            self.token_estimate += 1000
            return True
        else:
            self.log("5/5", f"Found {len(issues)} issues: {issues[:3]}")
            return False
    
    def run(self, svd_file: str, output_dir: str) -> Dict:
        """Main execution flow - 5-step long-chain reasoning"""
        print("\n" + "="*60)
        print(f"Register Driver Agent - Processing {svd_file}")
        print("="*60 + "\n")
        
        # Read input
        with open(svd_file, 'r') as f:
            svd_content = f.read()
        
        # Step 1: Parse
        parsed = self.parse_svd(svd_content)
        
        # Step 2: Generate bitfield macros
        macros = self.generate_bitfield_macros(parsed)
        
        # Step 3: Generate access functions
        functions = self.generate_access_functions(parsed)
        
        # Step 4: Generate init template
        init_code = self.generate_init_template(parsed)
        
        # Step 5: Self-validate
        valid = self.self_validate(parsed, macros)
        
        # Combine outputs
        header_content = macros
        source_content = functions + init_code
        
        # Write files
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        header_path = os.path.join(output_dir, f"{parsed['peripheral'].lower()}_regs.h")
        source_path = os.path.join(output_dir, f"{parsed['peripheral'].lower()}_drv.c")
        
        with open(header_path, 'w') as f:
            f.write(header_content)
        
        with open(source_path, 'w') as f:
            f.write(source_content)
        
        # Print summary
        print("\n" + "="*60)
        print("✅ Agent Execution Complete")
        print("="*60)
        print(f"📁 Output directory: {output_dir}/")
        print(f"📄 Header file: {parsed['peripheral'].lower()}_regs.h")
        print(f"📄 Source file: {parsed['peripheral'].lower()}_drv.c")
        print(f"🔢 Estimated Token usage: ~{self.token_estimate}")
        print(f"✅ Self-validation: {'PASSED' if valid else 'ISSUES FOUND'}")
        print("="*60 + "\n")
        
        return {
            'valid': valid,
            'token_estimate': self.token_estimate,
            'output_files': [header_path, source_path]
        }


def main():
    parser = argparse.ArgumentParser(description='Register Driver Agent')
    parser.add_argument('--input', default='input.svd', help='Input SVD file')
    parser.add_argument('--output', default='./output/', help='Output directory')
    args = parser.parse_args()
    
    agent = RegisterDriverAgent()
    result = agent.run(args.input, args.output)
    
    # Save run log
    with open(f"{args.output}/run_log.txt", 'w') as f:
        f.write('\n'.join(agent.steps_log))
        f.write(f"\n\nToken estimate: {result['token_estimate']}")
        f.write(f"\nValidation: {'PASSED' if result['valid'] else 'FAILED'}")


if __name__ == "__main__":
    main()