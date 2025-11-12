class ParamsTestController < ApplicationController
  def test_types
    result = analyze_params(params)
    render json: result
  end

  private

  def analyze_params(params)
    # 特殊なRailsパラメータを除外
    excluded_keys = ['controller', 'action', 'params_test']

    data = params.except(*excluded_keys)

    {
      received_params: data,
      type_analysis: analyze_recursive(data.to_unsafe_h)
    }
  end

  def analyze_recursive(obj)
    case obj
    when Hash
      obj.transform_values { |v| analyze_recursive(v) }
    when Array
      obj.map { |v| analyze_recursive(v) }
    else
      {
        value: obj,
        class: obj.class.name,
        type: determine_type(obj),
        is_string: obj.is_a?(String),
        is_numeric: obj.is_a?(Numeric),
        is_boolean: obj.is_a?(TrueClass) || obj.is_a?(FalseClass),
        is_nil: obj.nil?
      }
    end
  end

  def determine_type(obj)
    case obj
    when Integer
      'Integer'
    when Float
      'Float'
    when TrueClass, FalseClass
      'Boolean'
    when NilClass
      'Nil'
    when String
      'String'
    else
      obj.class.name
    end
  end
end
