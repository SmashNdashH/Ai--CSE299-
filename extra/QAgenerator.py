import json
import sys
import os
from collections import Counter

class ActStatistics:
    """
    Analyze and count statistics from Bangladesh Legal Acts dataset.
    """
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.data = None
        self.acts = []
        
    def load_data(self):
        """Load the JSON dataset."""
        print(f"Loading data from: {self.input_file}")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.acts = self.data.get('acts', [])
            print(f"✓ Successfully loaded dataset\n")
            return True
        except FileNotFoundError:
            print(f"✗ Error: File '{self.input_file}' not found")
            return False
        except json.JSONDecodeError:
            print(f"✗ Error: Invalid JSON format")
            return False
    
    def count_basic_stats(self):
        """Count basic statistics."""
        if not self.acts:
            self.load_data()
        
        total_acts = len(self.acts)
        total_sections = sum(len(act.get('sections', [])) for act in self.acts)
        
        print("="*70)
        print("BASIC STATISTICS")
        print("="*70)
        print(f"Total Acts:           {total_acts:,}")
        print(f"Total Sections:       {total_sections:,}")
        print(f"Average Sections/Act: {total_sections/total_acts:.2f}")
        print()
        
        return {
            'total_acts': total_acts,
            'total_sections': total_sections,
            'avg_sections': total_sections/total_acts
        }
    
    def count_by_year(self):
        """Count acts by year."""
        if not self.acts:
            self.load_data()
        
        year_counts = Counter()
        for act in self.acts:
            year = act.get('act_year', 'Unknown')
            year_counts[year] += 1
        
        print("="*70)
        print("ACTS BY YEAR")
        print("="*70)
        
        # Sort by year
        sorted_years = sorted(year_counts.items(), key=lambda x: (x[0] != 'Unknown', x[0]))
        
        print(f"{'Year':<12} {'Count':<10} {'Bar Chart'}")
        print("-"*70)
        
        for year, count in sorted_years[:20]:  # Show first 20
            bar = '█' * (count // 2) if count > 1 else '▌'
            print(f"{year:<12} {count:<10} {bar}")
        
        if len(sorted_years) > 20:
            print(f"... and {len(sorted_years) - 20} more years")
        
        print(f"\nTotal unique years: {len(year_counts)}")
        print()
        
        return year_counts
    
    def count_sections_distribution(self):
        """Show distribution of section counts."""
        if not self.acts:
            self.load_data()
        
        section_counts = [len(act.get('sections', [])) for act in self.acts]
        section_distribution = Counter(section_counts)
        
        print("="*70)
        print("SECTION COUNT DISTRIBUTION")
        print("="*70)
        
        # Statistics
        print(f"Min sections in an act:  {min(section_counts)}")
        print(f"Max sections in an act:  {max(section_counts)}")
        print(f"Average:                 {sum(section_counts)/len(section_counts):.2f}")
        print(f"Median:                  {sorted(section_counts)[len(section_counts)//2]}")
        print()
        
        # Distribution
        print(f"{'Sections':<15} {'Acts':<10} {'Percentage':<12} {'Bar'}")
        print("-"*70)
        
        sorted_dist = sorted(section_distribution.items())
        for num_sections, count in sorted_dist[:20]:
            percentage = (count / len(self.acts)) * 100
            bar = '█' * int(percentage / 2)
            print(f"{num_sections:<15} {count:<10} {percentage:>6.2f}%      {bar}")
        
        if len(sorted_dist) > 20:
            print(f"... and {len(sorted_dist) - 20} more categories")
        
        print()
        return section_distribution
    
    def find_extremes(self):
        """Find acts with most/least sections."""
        if not self.acts:
            self.load_data()
        
        # Sort by section count
        acts_with_counts = [(act, len(act.get('sections', []))) for act in self.acts]
        acts_with_counts.sort(key=lambda x: x[1], reverse=True)
        
        print("="*70)
        print("TOP 10 ACTS WITH MOST SECTIONS")
        print("="*70)
        
        for i, (act, count) in enumerate(acts_with_counts[:10], 1):
            title = act.get('act_title', 'Unknown')
            year = act.get('act_year', 'N/A')
            print(f"{i:2}. [{year}] {title[:55]}")
            print(f"    Sections: {count}")
            print()
        
        print("="*70)
        print("ACTS WITH NO SECTIONS")
        print("="*70)
        
        no_sections = [(act, 0) for act, count in acts_with_counts if count == 0]
        
        if no_sections:
            print(f"Found {len(no_sections)} acts with no sections:")
            for i, (act, _) in enumerate(no_sections[:10], 1):
                title = act.get('act_title', 'Unknown')
                year = act.get('act_year', 'N/A')
                print(f"{i:2}. [{year}] {title[:55]}")
            
            if len(no_sections) > 10:
                print(f"... and {len(no_sections) - 10} more")
        else:
            print("✓ All acts have at least one section!")
        
        print()
    
    def count_by_government(self):
        """Count acts by government system."""
        if not self.acts:
            self.load_data()
        
        gov_counts = Counter()
        
        for act in self.acts:
            gov_context = act.get('government_context', {})
            gov_system = gov_context.get('govt_system', 'Unknown')
            gov_counts[gov_system] += 1
        
        print("="*70)
        print("ACTS BY GOVERNMENT SYSTEM")
        print("="*70)
        
        sorted_govs = sorted(gov_counts.items(), key=lambda x: x[1], reverse=True)
        
        for gov_system, count in sorted_govs:
            percentage = (count / len(self.acts)) * 100
            bar = '█' * int(percentage / 2)
            print(f"{gov_system[:40]:<42} {count:>5} ({percentage:>5.1f}%) {bar}")
        
        print()
        return gov_counts
    
    def count_by_legal_period(self):
        """Count acts by legal period."""
        if not self.acts:
            self.load_data()
        
        period_counts = Counter()
        
        for act in self.acts:
            legal_context = act.get('legal_system_context', {})
            period_info = legal_context.get('period_info', {})
            period_name = period_info.get('period_name', 'Unknown')
            period_counts[period_name] += 1
        
        print("="*70)
        print("ACTS BY LEGAL PERIOD")
        print("="*70)
        
        sorted_periods = sorted(period_counts.items(), key=lambda x: x[1], reverse=True)
        
        for period_name, count in sorted_periods:
            percentage = (count / len(self.acts)) * 100
            bar = '█' * int(percentage / 2)
            print(f"{period_name[:40]:<42} {count:>5} ({percentage:>5.1f}%) {bar}")
        
        print()
        return period_counts
    
    def generate_full_report(self, output_file: str = "statistics_report.txt"):
        """Generate a complete statistics report."""
        if not self.acts:
            if not self.load_data():
                return
        
        # Redirect output to file
        import sys
        original_stdout = sys.stdout
        
        with open(output_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            
            print("BANGLADESH LEGAL ACTS - STATISTICAL ANALYSIS")
            print("="*70)
            print(f"Dataset: {self.input_file}")
            print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n")
            
            self.count_basic_stats()
            self.count_sections_distribution()
            self.find_extremes()
            self.count_by_year()
            self.count_by_government()
            self.count_by_legal_period()
            
            print("="*70)
            print("END OF REPORT")
            print("="*70)
        
        sys.stdout = original_stdout
        print(f"✓ Full report saved to: {output_file}")
    
    def quick_summary(self):
        """Display a quick summary."""
        if not self.acts:
            if not self.load_data():
                return
        
        total_acts = len(self.acts)
        total_sections = sum(len(act.get('sections', [])) for act in self.acts)
        
        print("\n" + "="*70)
        print("QUICK SUMMARY")
        print("="*70)
        print(f"📚 Total Acts:              {total_acts:,}")
        print(f"📄 Total Sections:          {total_sections:,}")
        print(f"📊 Average Sections/Act:    {total_sections/total_acts:.2f}")
        
        # Year range
        years = [act.get('act_year') for act in self.acts if act.get('act_year') != 'Unknown']
        if years:
            try:
                numeric_years = [int(y) for y in years if str(y).isdigit()]
                if numeric_years:
                    print(f"📅 Year Range:              {min(numeric_years)} - {max(numeric_years)}")
            except:
                pass
        
        # Most common section count
        section_counts = [len(act.get('sections', [])) for act in self.acts]
        most_common = Counter(section_counts).most_common(1)[0]
        print(f"🔢 Most Common Section Count: {most_common[0]} ({most_common[1]} acts)")
        
        print("="*70 + "\n")


def main():
    """Main execution function."""
    print("="*70)
    print("BANGLADESH LEGAL ACTS - STATISTICS COUNTER")
    print("="*70)
    print()
    
    # Try to find input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        possible_names = [
            'Contextualized_Bangladesh_Legal_Acts.json',
            'Contextualized_Bangladesh_Legal_Acts',
            'legal_acts_dataset.json',
            'all_acts_clean.txt',
            'contextualized_bangladesh_legal_acts.json',
            'bangladesh_legal_acts.json'
        ]
        
        input_file = None
        for name in possible_names:
            if os.path.exists(name):
                input_file = name
                break
        
        if not input_file:
            print("ERROR: No dataset file found!")
            print("Usage: python act_counter.py YOUR_FILE.json")
            sys.exit(1)
    
    # Create statistics object
    stats = ActStatistics(input_file)
    
    # Display menu
    while True:
        print("\nWhat would you like to see?")
        print("  1. Quick Summary")
        print("  2. Basic Statistics")
        print("  3. Section Distribution")
        print("  4. Acts by Year")
        print("  5. Acts by Government System")
        print("  6. Acts by Legal Period")
        print("  7. Top Acts (Most/Least Sections)")
        print("  8. Generate Full Report (save to file)")
        print("  9. Show All Statistics")
        print("  0. Exit")
        print()
        
        choice = input("Enter choice (0-9): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            stats.quick_summary()
        elif choice == '2':
            stats.count_basic_stats()
        elif choice == '3':
            stats.count_sections_distribution()
        elif choice == '4':
            stats.count_by_year()
        elif choice == '5':
            stats.count_by_government()
        elif choice == '6':
            stats.count_by_legal_period()
        elif choice == '7':
            stats.find_extremes()
        elif choice == '8':
            output = input("Save as (default: statistics_report.txt): ").strip()
            if not output:
                output = "statistics_report.txt"
            stats.generate_full_report(output)
        elif choice == '9':
            stats.quick_summary()
            stats.count_basic_stats()
            stats.count_sections_distribution()
            stats.find_extremes()
            stats.count_by_year()
            stats.count_by_government()
            stats.count_by_legal_period()
        else:
            print("Invalid choice. Please enter 0-9.")
        
        input("\nPress Enter to continue...")
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()