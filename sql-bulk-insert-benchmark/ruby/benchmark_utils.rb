# ベンチマークユーティリティ
require 'benchmark'
require 'json'
require 'fileutils'

class BenchmarkTimer
  attr_reader :name, :duration, :record_count

  def initialize(name)
    @name = name
    @start_time = nil
    @end_time = nil
    @duration = nil
    @record_count = 0
  end

  def measure(record_count)
    @record_count = record_count
    @start_time = Time.now

    begin
      yield
      success = true
      error = nil
    rescue => e
      success = false
      error = e.message
      puts "ERROR: #{error}"
    end

    @end_time = Time.now
    @duration = @end_time - @start_time

    {
      name: @name,
      duration_seconds: @duration.round(3),
      records_per_second: success ? (@record_count / @duration).round(2) : 0,
      record_count: @record_count,
      success: success,
      error: error,
      timestamp: Time.now.iso8601
    }
  end
end

class BenchmarkRunner
  attr_reader :results

  def initialize(output_file: '/results/ruby_benchmark_results.json')
    @output_file = output_file
    @results = []
  end

  def run_benchmark(name, record_count, &block)
    puts "\n#{'='*60}"
    puts "Running: #{name}"
    puts "Records: #{record_count.to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}"
    puts "#{'='*60}"

    timer = BenchmarkTimer.new(name)
    result = timer.measure(record_count, &block)

    if result[:success]
      puts "✓ Completed in #{result[:duration_seconds]}s"
      puts "  Throughput: #{result[:records_per_second].to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse} records/sec"
    else
      puts "✗ Failed: #{result[:error]}"
    end

    @results << result
    result
  end

  def save_results
    FileUtils.mkdir_p(File.dirname(@output_file))

    # 既存の結果を読み込み
    existing_results = []
    if File.exist?(@output_file)
      begin
        existing_results = JSON.parse(File.read(@output_file))
      rescue
        # JSONパースエラーは無視
      end
    end

    # 新しい結果を追加
    existing_results.concat(@results)

    # 保存
    File.write(@output_file, JSON.pretty_generate(existing_results))
    puts "\n✓ Results saved to #{@output_file}"
  end

  def print_summary
    puts "\n#{'='*60}"
    puts "BENCHMARK SUMMARY"
    puts "#{'='*60}"

    successful = @results.select { |r| r[:success] }
    failed = @results.reject { |r| r[:success] }

    puts "\nTotal benchmarks: #{@results.size}"
    puts "Successful: #{successful.size}"
    puts "Failed: #{failed.size}"

    if successful.any?
      puts "\n#{'Method':<40} #{'Records/sec':>15}"
      puts '-' * 60
      successful.sort_by { |r| -r[:records_per_second] }.each do |r|
        rps = r[:records_per_second].to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse
        puts "#{r[:name][0...40].ljust(40)} #{rps.rjust(15)}"
      end
    end
  end
end
