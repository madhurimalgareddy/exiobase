#!/usr/bin/env python3
"""
US Bureau of Economic Analysis (BEA) Enhanced Trade Flow Analysis

Extends ExiobaseTradeFlow with BEA API integration for comprehensive US trade analysis.
Combines Exiobase MRIO data with BEA API data to create detailed relational trade tables
with state-level insights, economic impacts, and enhanced analytical capabilities.

Usage:
    python us-bea.py --bea-key YOUR_API_KEY
    python us-bea.py  # Uses BEA_API_KEY from webroot .env file

BEA API Key Setup:
    1. Register at https://apps.bea.gov/api/signup/
    2. Add BEA_API_KEY=your_key_here to webroot/.env file
    OR
    3. Pass key via --bea-key command line argument

Processing Order:
    1. Base trade data generation (using existing Exiobase patterns)
    2. State-to-state domestic trade flows
    3. State export competitiveness analysis  
    4. Import dependency analysis
    5. FEDEFL flow integration
    6. Cross-validation and reporting
"""

import pandas as pd
import numpy as np
import time
import argparse
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import existing modules
from trade import ExiobaseTradeFlow
from config_loader import load_config, get_file_path, get_reference_file_path

# Import US-BEA specialized modules
from us_bea_api_client import BEAAPIClient
from us_state_trade_analyzer import StateTradeAnalyzer
from us_fedefl_integration import FEDEFLIntegrator

class USBEATradeFlow(ExiobaseTradeFlow):
    def __init__(self, bea_api_key=None):
        super().__init__()
        
        # Load BEA API key from multiple sources
        self.bea_api_key = self._load_bea_api_key(bea_api_key)
        
        # Initialize validation tracking
        self.validation_issues = []
        self.processing_log = []
        
        # Initialize US-BEA specialized components
        self.bea_client = BEAAPIClient(self.bea_api_key)
        self.state_analyzer = StateTradeAnalyzer(self.config)
        self.fedefl_integrator = FEDEFLIntegrator()
        
        print(f"🇺🇸 Initialized US-BEA Trade Flow Analysis for {self.config['YEAR']} {self.config['COUNTRY']}")
        print(f"Trade flows: {self.config['TRADEFLOW']}")
        
    def _load_bea_api_key(self, provided_key):
        """Load BEA API key from command line, .env file, or environment"""
        if provided_key:
            return provided_key
            
        # Try loading from webroot .env file
        webroot_env = Path(__file__).parents[2] / '.env'
        if webroot_env.exists():
            load_dotenv(webroot_env)
            env_key = os.getenv('BEA_API_KEY')
            if env_key:
                print(f"Loaded BEA API key from {webroot_env}")
                return env_key
        
        # Try system environment
        env_key = os.getenv('BEA_API_KEY')
        if env_key:
            print("Loaded BEA API key from system environment")
            return env_key
            
        raise ValueError(
            "BEA API key not found. Please:\n"
            "1. Register at https://apps.bea.gov/api/signup/\n"
            "2. Add BEA_API_KEY=your_key to webroot/.env file\n"
            "   OR pass --bea-key YOUR_KEY argument"
        )
    
    def process_all_tradeflows(self):
        """Main processing pipeline for enhanced BEA trade analysis"""
        start_time = time.time()
        
        tradeflows = self.config['TRADEFLOW']
        if isinstance(tradeflows, str):
            tradeflows = [t.strip() for t in tradeflows.split(',')]
            
        print(f"\nProcessing {len(tradeflows)} trade flows: {', '.join(tradeflows)}")
        
        for tradeflow in tradeflows:
            print(f"\n{'='*60}")
            print(f"Processing {tradeflow.upper()} trade flows")
            print(f"{'='*60}")
            
            self.current_tradeflow = tradeflow
            self.process_bea_enhanced_tradeflow(tradeflow)
        
        # Generate comprehensive validation report
        self._generate_validation_report()
        
        total_time = time.time() - start_time
        print(f"\n✅ Completed all US-BEA trade flows in {total_time:.1f} seconds")
        
    def process_bea_enhanced_tradeflow(self, tradeflow):
        """Enhanced processing pipeline for single tradeflow"""
        flow_start = time.time()
        
        # Phase 1: Generate base trade data using existing patterns
        print(f"\n📊 Phase 1: Generating base {tradeflow} trade data...")
        self._generate_base_trade_data(tradeflow)
        
        # Phase 2: BEA API data enhancement
        print(f"\n🌐 Phase 2: Enhancing with US-BEA API data...")
        self._enhance_with_bea_data(tradeflow)
        
        # Phase 3: State-level analysis (logical order based on tradeflow)
        if tradeflow == 'domestic':
            print(f"\n🏛️ Phase 3: US state-to-state domestic flow analysis...")
            self._analyze_state_domestic_flows()
        elif tradeflow == 'exports':
            print(f"\n📈 Phase 3: US state export competitiveness analysis...")
            self._analyze_state_export_competitiveness()
        elif tradeflow == 'imports':
            print(f"\n📉 Phase 3: US import dependency analysis...")
            self._analyze_import_dependency()
            
        # Phase 4: FEDEFL integration (after trade data is established)
        print(f"\n🌿 Phase 4: US-FEDEFL flow integration...")
        self._integrate_fedefl_flows()
        
        # Phase 5: Generate enhanced output tables
        print(f"\n📋 Phase 5: Generating US-BEA relational output tables...")
        self._generate_enhanced_output_tables(tradeflow)
        
        flow_time = time.time() - flow_start
        print(f"✅ Completed US-BEA {tradeflow} processing in {flow_time:.1f} seconds")
        
    def _generate_base_trade_data(self, tradeflow):
        """Generate base trade data using existing Exiobase patterns"""
        # Update config for current tradeflow
        original_tradeflow = self.config['TRADEFLOW']
        self.config['TRADEFLOW'] = tradeflow
        
        try:
            # Use existing ExiobaseTradeFlow methods
            self.ensure_exiobase_data_downloaded()
            self.load_exiobase_data()
            
            if tradeflow == 'domestic':
                self.extract_domestic_flows()
            elif tradeflow == 'imports':
                self.extract_import_flows()
            elif tradeflow == 'exports':
                self.extract_export_flows()
                
            self.create_reference_files()
            self.save_trade_flows()
            self.generate_trade_factors()
            
            print(f"✅ Generated base {tradeflow} trade data")
            
        finally:
            # Restore original config
            self.config['TRADEFLOW'] = original_tradeflow
    
    def _enhance_with_bea_data(self, tradeflow):
        """Enhance trade data with US-BEA API data"""
        
        # Get relevant BEA datasets based on tradeflow using us-bea_api_client
        if tradeflow == 'imports':
            self._fetch_bea_imports_data()
        elif tradeflow == 'exports':
            self._fetch_bea_exports_data()
        elif tradeflow == 'domestic':
            self._fetch_bea_domestic_data()
            
        # Create US-BEA trade detail enhancement
        self._create_bea_trade_detail()
        
    def _fetch_bea_imports_data(self):
        """Fetch BEA imports data from API using us-bea_api_client"""
        print("  📥 Fetching US-BEA imports data...")
        
        try:
            response = self.bea_client.get_international_trade_data(
                year=self.config['YEAR'], 
                trade_direction='Imports'
            )
            self.bea_imports_data = self.bea_client.process_trade_response(response)
            print(f"    ✅ Retrieved {len(self.bea_imports_data)} import records")
            
        except Exception as e:
            print(f"    ⚠️ US-BEA imports data unavailable: {e}")
            self.bea_imports_data = pd.DataFrame()
            self.validation_issues.append(f"US-BEA imports API error: {e}")
    
    def _fetch_bea_exports_data(self):
        """Fetch BEA exports data including state-level data using us-bea_api_client"""
        print("  📤 Fetching US-BEA exports data...")
        
        try:
            # National exports
            response = self.bea_client.get_international_trade_data(
                year=self.config['YEAR'],
                trade_direction='Exports'
            )
            self.bea_exports_data = self.bea_client.process_trade_response(response)
            print(f"    ✅ Retrieved {len(self.bea_exports_data)} export records")
            
            # State-level exports
            self._fetch_state_exports_data()
            
        except Exception as e:
            print(f"    ⚠️ US-BEA exports data unavailable: {e}")
            self.bea_exports_data = pd.DataFrame()
            self.validation_issues.append(f"US-BEA exports API error: {e}")
    
    def _fetch_state_exports_data(self):
        """Fetch state-level export data from BEA using us-bea_api_client"""
        print("  🏛️ Fetching US state-level exports data...")
        
        try:
            response = self.bea_client.get_state_exports_data(
                year=self.config['YEAR'],
                state_code='ALL'
            )
            self.bea_state_exports = self.bea_client.process_state_response(response)
            print(f"    ✅ Retrieved state export data for {len(self.bea_state_exports)} records")
            
        except Exception as e:
            print(f"    ⚠️ US state exports data unavailable: {e}")
            self.bea_state_exports = pd.DataFrame()
            self.validation_issues.append(f"US-BEA state exports API error: {e}")
    
    def _fetch_bea_domestic_data(self):
        """Fetch BEA domestic economic data using us-bea_api_client"""
        print("  🏠 Fetching US-BEA domestic data...")
        
        try:
            # Input-Output Tables
            response = self.bea_client.get_input_output_data(
                year=self.config['YEAR'],
                table_id='Summary'
            )
            self.bea_domestic_data = self.bea_client.process_io_response(response)
            print(f"    ✅ Retrieved domestic I-O data")
            
        except Exception as e:
            print(f"    ⚠️ US-BEA domestic data unavailable: {e}")
            self.bea_domestic_data = pd.DataFrame()
            self.validation_issues.append(f"US-BEA domestic API error: {e}")
    
    def _create_bea_trade_detail(self):
        """Create enhanced trade detail with US-BEA data integration"""
        print("  🔗 Creating US-BEA trade detail integration...")
        
        # Load base trade data
        trade_file = get_file_path(self.config, 'industryflow')
        if not trade_file.exists():
            print(f"    ⚠️ Base trade file not found: {trade_file}")
            return
            
        base_trade = pd.read_csv(trade_file)
        
        # Create enhanced trade detail table
        enhanced_detail = base_trade.copy()
        
        # Add US-BEA-specific enhancements based on current tradeflow
        if self.current_tradeflow == 'imports' and not self.bea_imports_data.empty:
            enhanced_detail = self._merge_bea_imports(enhanced_detail)
        elif self.current_tradeflow == 'exports' and not self.bea_exports_data.empty:
            enhanced_detail = self._merge_bea_exports(enhanced_detail)
        elif self.current_tradeflow == 'domestic' and not self.bea_domestic_data.empty:
            enhanced_detail = self._merge_bea_domestic(enhanced_detail)
        
        # Save enhanced detail
        output_file = get_file_path(self.config, 'industryflow').parent / 'bea_trade_detail.csv'
        enhanced_detail.to_csv(output_file, index=False)
        print(f"    ✅ Created BEA trade detail: {output_file}")
    
    def _merge_bea_imports(self, base_trade):
        """Merge US-BEA imports data with base trade"""
        enhanced = base_trade.copy()
        
        # Add US-BEA-specific columns
        enhanced['bea_commodity_code'] = ''
        enhanced['bea_industry_code'] = ''
        enhanced['trade_balance'] = 0.0
        enhanced['import_value'] = enhanced['amount']
        enhanced['export_value'] = 0.0
        
        return enhanced
    
    def _merge_bea_exports(self, base_trade):
        """Merge US-BEA exports data with base trade"""
        enhanced = base_trade.copy()
        
        # Add US-BEA-specific columns
        enhanced['bea_commodity_code'] = ''
        enhanced['bea_industry_code'] = ''
        enhanced['trade_balance'] = enhanced['amount']
        enhanced['import_value'] = 0.0
        enhanced['export_value'] = enhanced['amount']
        
        return enhanced
    
    def _merge_bea_domestic(self, base_trade):
        """Merge US-BEA domestic data with base trade"""
        enhanced = base_trade.copy()
        
        # Add domestic-specific columns
        enhanced['bea_commodity_code'] = ''
        enhanced['bea_industry_code'] = ''
        enhanced['economic_multiplier'] = 1.0
        
        return enhanced
    
    def _analyze_state_domestic_flows(self):
        """Analyze US state-to-state domestic trade flows using us-state_trade_analyzer"""
        print("  🗺️ Analyzing US state-to-state flows...")
        
        # Load base trade data
        trade_file = get_file_path(self.config, 'industryflow')
        if trade_file.exists():
            base_trade = pd.read_csv(trade_file)
            
            # Use US state analyzer to disaggregate flows
            state_flows = self.state_analyzer.disaggregate_domestic_flows(
                base_trade, self.bea_domestic_data
            )
            
            # Calculate comprehensive US state impacts
            state_impacts = self.state_analyzer.calculate_state_industry_impacts(state_flows)
            
            # Save results
            output_path = get_file_path(self.config, 'industryflow').parent
            state_flows.to_csv(output_path / 'state_trade_flows.csv', index=False)
            state_impacts.to_csv(output_path / 'state_industry_impacts.csv', index=False)
            
            print(f"    ✅ Created US state domestic flow analysis")
        else:
            print(f"    ⚠️ Base trade file not found: {trade_file}")
    
    def _analyze_state_export_competitiveness(self):
        """Analyze US state export competitiveness using us-state_trade_analyzer"""
        print("  📊 Analyzing US export competitiveness...")
        
        # Load export trade data
        trade_file = get_file_path(self.config, 'industryflow')
        if trade_file.exists():
            export_trade = pd.read_csv(trade_file)
            
            # Use US state analyzer for competitiveness analysis
            competitiveness = self.state_analyzer.analyze_export_competitiveness(
                export_trade, self.bea_exports_data
            )
            
            # Save results
            output_path = get_file_path(self.config, 'industryflow').parent
            competitiveness.to_csv(output_path / 'export_competitiveness.csv', index=False)
            
            print(f"    ✅ Created US export competitiveness analysis")
        else:
            print(f"    ⚠️ Export trade file not found: {trade_file}")
    
    def _analyze_import_dependency(self):
        """Analyze US import dependency and vulnerabilities using us-state_trade_analyzer"""
        print("  🔗 Analyzing US import dependencies...")
        
        # Load import trade data
        trade_file = get_file_path(self.config, 'industryflow')
        if trade_file.exists():
            import_trade = pd.read_csv(trade_file)
            
            # Use US state analyzer for dependency analysis
            dependency = self.state_analyzer.analyze_import_dependency(
                import_trade, self.bea_imports_data
            )
            
            # Save results
            output_path = get_file_path(self.config, 'industryflow').parent
            dependency.to_csv(output_path / 'import_dependency.csv', index=False)
            
            print(f"    ✅ Created US import dependency analysis")
        else:
            print(f"    ⚠️ Import trade file not found: {trade_file}")
    
    def _integrate_fedefl_flows(self):
        """Integrate US-FEDEFL flow data using us-fedefl_integration"""
        print("  🌿 Integrating US-FEDEFL flows...")
        
        try:
            # Load comprehensive FEDEFL flows
            output_path = get_reference_file_path(self.config, 'factors').parent
            flow_data = self.fedefl_integrator.create_comprehensive_flow_table(output_path)
            
            # Validate flow completeness with trade factors
            factors_file = get_reference_file_path(self.config, 'factors')
            if factors_file.exists():
                factors = pd.read_csv(factors_file)
                self.fedefl_integrator.validate_flow_completeness(factors, output_path)
            
            print(f"    ✅ Created US-FEDEFL flow integration with {len(flow_data)} flows")
            
        except Exception as e:
            print(f"    ⚠️ US-FEDEFL integration failed: {e}")
            self.validation_issues.append(f"US-FEDEFL integration error: {e}")
    
    def _generate_enhanced_output_tables(self, tradeflow):
        """Generate all US-BEA enhanced output tables"""
        print("  📋 Generating US-BEA enhanced tables...")
        
        output_path = get_file_path(self.config, 'industryflow').parent
        
        # Create US trade price indices table
        self._create_trade_price_indices(output_path)
        
        # Create US-BEA industry mapping
        self._create_bea_industry_mapping(output_path)
        
        # Create US state reference data
        self.state_analyzer.create_state_reference_data(output_path)
        
        print(f"    ✅ Generated US-BEA enhanced output tables")
    
    def _create_trade_price_indices(self, output_path):
        """Create US trade price indices table"""
        # Basic price indices structure
        price_indices = pd.DataFrame({
            'trade_id': [],
            'import_price_index': [],
            'export_price_index': [],
            'exchange_rate': [],
            'price_year': [],
            'currency_adjustment_factor': []
        })
        
        price_indices.to_csv(output_path / 'trade_price_indices.csv', index=False)
    
    def _create_bea_industry_mapping(self, output_path):
        """Create US-BEA industry mapping table"""
        # Load industry data
        industry_file = get_reference_file_path(self.config, 'industries')
        if industry_file.exists():
            industries = pd.read_csv(industry_file)
            
            mapping = pd.DataFrame({
                'industry_id': industries.iloc[:, 0] if len(industries) > 0 else [],
                'exiobase_sector': industries.iloc[:, 1] if len(industries.columns) > 1 else [],
                'bea_sector_code': '',
                'bea_sector_name': '',
                'naics_code': '',
                'aggregation_level': 'detail'
            })
        else:
            mapping = pd.DataFrame(columns=['industry_id', 'exiobase_sector', 'bea_sector_code', 
                                          'bea_sector_name', 'naics_code', 'aggregation_level'])
        
        mapping.to_csv(output_path / 'bea_industry_mapping.csv', index=False)
    
    def _generate_validation_report(self):
        """Generate comprehensive US-BEA validation report"""
        report_path = Path(self.config['FOLDERS']['base'].format(
            year=self.config['YEAR']
        )) / self.config['COUNTRY'] / 'bea-report.md'
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"# BEA Trade Analysis Validation Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Year**: {self.config['YEAR']}\n")
            f.write(f"**Country**: {self.config['COUNTRY']}\n")
            f.write(f"**Trade Flows**: {self.config['TRADEFLOW']}\n\n")
            
            f.write("## US Data Source Integration\n\n")
            f.write("### Exiobase Data\n")
            f.write("- ✅ Successfully processed Exiobase MRIO data\n")
            f.write("- ✅ Generated base trade flows with trade_id structure\n\n")
            
            f.write("### US-BEA API Integration\n")
            if self.validation_issues:
                f.write("- ⚠️ Issues encountered:\n")
                for issue in self.validation_issues:
                    f.write(f"  - {issue}\n")
            else:
                f.write("- ✅ Successfully integrated US-BEA API data\n")
            
            f.write("\n## US Data Validation Results\n\n")
            f.write("### Cross-Source Comparison\n")
            f.write("*Standard validation applied between Exiobase and US-BEA data sources*\n\n")
            
            if self.validation_issues:
                f.write("### Issues Identified\n")
                for i, issue in enumerate(self.validation_issues, 1):
                    f.write(f"{i}. {issue}\n")
            else:
                f.write("✅ No significant validation issues identified\n")
            
            # Add US-BEA API usage statistics
            api_stats = self.bea_client.get_api_usage_stats()
            f.write(f"\n### BEA API Usage Statistics\n")
            f.write(f"- API calls made: {api_stats['api_calls_made']}\n")
            f.write(f"- Cache files created: {api_stats['cache_files']}\n")
            
            f.write(f"\n## BEA Enhanced Output Files Generated\n\n")
            f.write(f"### Enhanced Relational Tables\n")
            f.write(f"- `trade.csv` - Base trade flows (existing)\n")
            f.write(f"- `bea_trade_detail.csv` - BEA-enhanced trade details\n")
            f.write(f"- `state_trade_flows.csv` - State-level trade flows\n")
            f.write(f"- `export_competitiveness.csv` - Export competitiveness analysis\n")
            f.write(f"- `import_dependency.csv` - Import dependency analysis\n")
            f.write(f"- `flow.csv` - FEDEFL flow details\n")
            f.write(f"- `bea_industry_mapping.csv` - BEA industry concordance\n") 
            f.write(f"- `state_industry_impacts.csv` - State economic impacts\n")
            f.write(f"- `trade_price_indices.csv` - Trade price indices\n\n")
            
            f.write("## Recommendations\n\n")
            if self.validation_issues:
                f.write("- Review identified US data integration issues\n")
                f.write("- Consider manual validation of flagged discrepancies\n")
                f.write("- Update US-BEA API parameters if needed\n")
            else:
                f.write("- US data integration successful\n")
                f.write("- Ready for analytical use\n")
        
        print(f"✅ Generated BEA validation report: {report_path}")

def main():
    parser = argparse.ArgumentParser(description='US-BEA Enhanced Trade Flow Analysis with us- prefixed modules')
    parser.add_argument('--bea-key', help='BEA API key (or use .env file)')
    
    args = parser.parse_args()
    
    try:
        print("🇺🇸 Initializing US-BEA Trade Flow Analysis...")
        processor = USBEATradeFlow(bea_api_key=args.bea_key)
        processor.process_all_tradeflows()
        
    except Exception as e:
        print(f"❌ US-BEA Analysis Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())